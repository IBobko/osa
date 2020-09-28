import csv, json, os, tempfile
from urlparse import urlparse
from StringIO import StringIO
from poaupdater.uConst import *
from poaupdater.uDLCommon import HelmPackage
from poaupdater.uK8s import K8s, Repo
from poaupdater import openapi, uAction, uBuild, uK8s, uLogging, uUtil

def get_scripted_values(script_filename):
    globals = {}
    locals = dict(values='')
    try:
        execfile(script_filename, globals, locals)
    except SystemExit, e:
        if e.code:
            raise Exception("Execution of update script %s exited with non-zero error code: %s" % (script_filename, e.code))
    return locals['values']


class pendingPodsException(Exception):
    def __init__(self, pendingPods):
        Exception.__init__(self, "The following pods are in Pending state in Kubernetes cluster:\n %s This may indicate lack of resources of other problems with the cluster!" % pendingPods)

class notEnoughResourcesException(Exception):
    def __init__(self, type, pkg):
        Exception.__init__(self, "Remaining %s capacity in Kubernetes cluster is not enough for upgrade of packages (%s)!" % (type, pkg))


class Helm(object):


    def __init__(self, k8s_repo_url = uK8s.default_helm_repo_prefix, k8s_docker_repo_host = uK8s.default_k8s_docker_repo_host):
        self.k8s_repo_url = k8s_repo_url
        self.k8s_docker_repo_host = k8s_docker_repo_host
        uAction.retriable(self._init_helm)()


    def _init_helm(self):
        self._K8S = K8s()
        self._HAS_HELM = self._checkHelm()


    def _setSystemProperty(self, name, value):
        openapi.OpenAPI().pem.setSystemProperty(account_id=1, name=name, str_value=value)


    def _getHelmCommand(self):
        return self._K8S.get_helm_cmd()


    def _checkHelm(self):
        try:
            command = '%s help' % self._getHelmCommand()
            uLogging.info('Check Helm: %s' % command)
            uUtil.execCommand(command)
            return True
        except:
            uLogging.warn('Helm not found.')
            return False


    def _getKubernetesDockerRepositoryHost(self):
        try:
            return openapi.OpenAPI().pem.getSystemProperty(account_id=1, name='kubernetes_docker_repository_host')['str_value']
        except:
            return None


    def _fillHelmPackageValuesFile(self, pkg, values_file):
        if pkg.script:
            values_file.write(get_scripted_values(pkg.script))
            values_file.flush()


    def _loadsDeployedReleases(self):
        command = '%s list --output json' % self._getHelmCommand()
        uLogging.info('Loads deployed releases: %s' % command)
        output = uUtil.readCmd(command)
        if not output: output = '{}'
        return json.loads(output).get('Releases', [])


    def _listDeployedReleases(self):
        releases = list(filter(lambda x: x.get('Name') and x.get('Chart'), self._loadsDeployedReleases()))
        return list(map(lambda x: HelmPackage(x.get('Name'), x.get('Chart')).grabVersionFromChart(), releases))


    def _loadsLatestCharts(self, repoName):
        command = '%s search %s/' % (self._getHelmCommand(), repoName)
        uLogging.info('Loads latest charts: %s' % command)
        charts = list(csv.reader(StringIO(uUtil.readCmd(command)), delimiter='\t'))
        charts = [list(map(str.strip, x)) for x in charts]
        charts[0] = list(map(lambda x: x.title().replace(' ', ''), charts[0]))
        return list(map(lambda x: dict(zip(charts[0], x)), charts[1:]))


    def _searchLatestCharts(self):
        charts = list(filter(lambda x: x.get('Name') and x.get('ChartVersion'), self._loadsLatestCharts(Repo.helm_repo_name)))
        return list(map(lambda x: HelmPackage('', x.get('Name'), x.get('ChartVersion')), charts))


    def _resolveLatestVersions(self, pkgs):
        latestMap = dict((x.getChartRepoLess(), x) for x in self._searchLatestCharts())
        for pkg in pkgs:
            if not pkg.version: pkg.version = 'latest'
            if pkg.version != 'latest': continue
            latest = latestMap.get(pkg.getChartRepoLess())
            if not latest: continue
            pkg.version = latest.version
        return pkgs


    def _getNewestPackages(self, newPkgs, pkgs, skipNotDeployed):
        pkgsMap = dict((z.key(), z) for z in filter(lambda x: x.version, pkgs))
        return list(filter(lambda x: uBuild.compare_versions(x.version, pkgsMap.get(x.key(), HelmPackage('', '', 'latest' if skipNotDeployed else '0')).version) > 0, newPkgs))


    def _dumpPackageValues(self, pkg, reuse_values_file_path):
        command = '%s get values --all %s > %s' % (self._getHelmCommand(), pkg.name, reuse_values_file_path)
        uUtil.readCmd(command, valid_codes=[0, 1])
        return command


    def _upgradeHelmPackage(self, pkg, reuse_values_file_path):
        command = '%s upgrade %s %s --wait' % (self._getHelmCommand(), pkg.name, pkg.chart)
        if pkg.group and (pkg.group == HelmGroup.FOUNDATION or pkg.group == HelmGroup.REQUIRED):
            command = '%s --install' % command
        if pkg.version and pkg.version != 'latest':
            command = '%s --version %s' % (command, pkg.version)
        command = '%s -f %s' % (command, reuse_values_file_path)
        dockerRepo = self._getKubernetesDockerRepositoryHost()
        if dockerRepo:
            command = '%s --set dockerrepo=%s' % (command, dockerRepo)
        with tempfile.NamedTemporaryFile() as values_file:
            command = '%s -f %s' % (command, values_file.name)
            self._fillHelmPackageValuesFile(pkg, values_file)
            uLogging.info('Upgrade Helm package: %s (%s)' % (command, pkg.script))
            uUtil.readCmd(command)
        return command


    def _upgradeHelmPackageEx(self, pkg):
        with tempfile.NamedTemporaryFile() as reuse_values_file:
            self._dumpPackageValues(pkg, reuse_values_file.name)
            return self._upgradeHelmPackage(pkg, reuse_values_file.name)

    def _upgradeHelmPackagesGroup(self, helms_to_update, deployedReleases, group):
        uLogging.info('Upgrade Helm packages group: %s' % group)
        pkgs = helms_to_update.get(group)
        if not pkgs: return
        for pkg in self._getNewestPackages(pkgs, deployedReleases, group == HelmGroup.OPTIONAL):
            uAction.retriable(self._upgradeHelmPackageEx)(pkg)


    def _upgradeHelmPackages(self, helms_to_update, groups_to_update):
        if not helms_to_update: return
        uAction.retriable(self._resolveLatestVersions)(sum(helms_to_update.values(), []))
        deployedReleases = uAction.retriable(self._listDeployedReleases)()
        if deployedReleases is None: return
        for group in groups_to_update:
            self._upgradeHelmPackagesGroup(helms_to_update, deployedReleases, group)

    def _getUpgradeRequirements(self, deployedReleases, pkgs_to_upgrade):
        res = {}
        for pkg in deployedReleases:
            if pkg.name in pkgs_to_upgrade:
                res[pkg.name] = self._K8S.getUpgradeResourceRequiment(pkg.name)

        return res

    def _checkUpgradeHelmPackages(self, helm_packages):
        if not helm_packages: return
        deployedReleases = self._listDeployedReleases()
        if deployedReleases is None: return
        pkgs_to_upgrade = list(map(lambda x: x.name, helm_packages))
        #required_cpu, required_memory, pkg_name_cpu, pkg_name_memory = self._getUpgradeRequirements(deployedReleases, pkgs_to_upgrade)
        pkgRequirements = self._getUpgradeRequirements(deployedReleases, pkgs_to_upgrade)
        nodesCapacity = self._K8S.getNodesAvailableResources()
        for pkgName in pkgRequirements:
            uLogging.info("Package: %s" % pkgName)
            
            (reqCpu, reqMem) = pkgRequirements[pkgName]
            uLogging.info("Requires: %s cpu, %s mem" % (reqCpu, reqMem))
            fitNode = None
            fitCpu = fitMemory = True
            for nodeCapacity in nodesCapacity:
                (nodeCpu, nodeMem) = nodeCapacity
                uLogging.info("Node resources: %s cpu, %s mem" % (nodeCpu, nodeMem))
                if reqCpu < nodeCpu and reqMem < nodeMem:
                    # pod fits in the node
                    fitNode = nodeCapacity
                    fitCpu = fitMemory = True
                    break
                if reqCpu < nodeCpu:
                    fitMemory = False
                else:
                    fitCpu = False

            if fitNode is None:
                if not fitCpu:
                    raise notEnoughResourcesException('cpu', pkgName)
                if not fitMemory:
                    raise notEnoughResourcesException('memory', pkgName)

        pendingPods = self._K8S.getPendingPods()
        if pendingPods:
            uLogging.warn("The following pods are in Pending state in Kubernetes cluster:\n %s This may indicate lack of resources of other problems with the cluster!" % pendingPods)

    def _updateHelmRepo(self):
        command = ' %s repo update' % self._getHelmCommand()
        uLogging.info('Update Helm repository: %s' % command)
        uUtil.readCmd(command)


    def _upgradeHelmRepo(self, version):
        uLogging.info('Upgrade Helm repository to version: %s' % version)
        repo = self._K8S.get_helm_repo()
        if not repo.is_upgradable_url(): return
        command = self._K8S.get_custom_helm_repo_add_cmd(repo, version)
        uUtil.readCmd(command)


    def _setupHelmRepo(self, version):
        repo = uK8s.Repo(prefix=self.k8s_repo_url)
        repo_url = repo.custom_url(version)
        uLogging.info('Setup Helm repository: %s' % repo_url)
        command = self._K8S.get_custom_helm_repo_add_cmd(repo, version)
        uUtil.readCmd(command)


    def _setupDockerRepo(self):
        uLogging.info('Setup Docker repository host: %s' % self.k8s_docker_repo_host)
        self._setSystemProperty('kubernetes_docker_repository_host', self.k8s_docker_repo_host)
        command = self._K8S.get_image_pull_secrets_patch_cmd()
        uUtil.readCmd(command)
        # Note: 'secret' will be installed with requred component: 'repo-config' helm chart


    def _setupRepos(self, version):
        self._setupHelmRepo(version)
        self._setupDockerRepo()


    def _setupK8sApiUrl(self):
        api_url = uUtil.readCmd('kubectl config view -o jsonpath="{.clusters[*].cluster.server}"')
        uLogging.info('Setup Kubernetes API URL: %s' % api_url)
        self._setSystemProperty('kubernetes_api', api_url)


    def _setupK8sApiToken(self):
        token = uUtil.readCmd("kubectl get secret -n kube-system $(kubectl get secrets -n kube-system | grep tiller | cut -f1 -d ' ') -o jsonpath={.data.token} | base64 -d")
        self._setSystemProperty('kubernetes_token', token)


    def _setupK8sApiCertificate(self):
        cert = '/usr/local/pem/kubernetes/certs/kubernetesApi.pem'
        uLogging.info('Setup Kubernetes API certificate: %s' % cert)
        cmds = []
        cmds.append("mkdir -p /usr/local/pem/kubernetes/certs/")
        cmds.append("grep 'certificate-authority-data' /root/.kube/config | awk '{print $2}' | base64 -d > %s" % cert)
        cmds.append("chown jboss:jboss %s" % cert)
        cmds.append("chmod 0400 %s" % cert)
        map(uUtil.readCmd, cmds)


    def _setupK8sApi(self):
        self._setupK8sApiUrl()
        self._setupK8sApiToken()
        self._setupK8sApiCertificate()


    def _getHelmUpgradeClientCommands(self):
        tempDirName = '/tmp/upgrade_helm'
        createDir = 'mkdir %s' % tempDirName
        return [createDir] + self._K8S.get_helm_client_install_cmds(tempDirName)


    def _getHelmUpgradeServerCommands(self):
        command = '%s init --upgrade --wait' % self._getHelmCommand()
        return [command]


    def getHelmUpgradeCommands(self):
        return self._getHelmUpgradeClientCommands() + self._getHelmUpgradeServerCommands()


    def getTargetHelmVersion(self):
        return uK8s.helm_version


    def _isHelmUpgradeClientRequired(self):
        command = '%s version --client --template {{.Client.SemVer}}' % self._getHelmCommand()
        version = uUtil.readCmd(command)
        return uBuild.compare_versions(self.getTargetHelmVersion(), version) > 0


    def _isHelmUpgradeServerRequired(self):
        command = '%s version --server --template {{.Server.SemVer}}' % self._getHelmCommand()
        version = uUtil.readCmd(command)
        return uBuild.compare_versions(self.getTargetHelmVersion(), version) > 0


    def isHelmUpgradeRequired(self):
        return self._isHelmUpgradeClientRequired() or self._isHelmUpgradeServerRequired()


    def isHelmInstalled(self):
        return self._HAS_HELM


    def checkCapacityForUpgrade(self, helms_to_update):
        if not self.isHelmInstalled(): return
        self._checkUpgradeHelmPackages(helms_to_update)
        uLogging.info('Kubernetes cluster has enough resources for upgrade')


    def upgrade(self, helms_to_update, repo_version):
        if not self.isHelmInstalled(): return
        uAction.retriable(self._upgradeHelmRepo)(repo_version)
        uAction.retriable(self._updateHelmRepo)()
        groups_to_update = [HelmGroup.FOUNDATION, HelmGroup.REQUIRED, HelmGroup.OPTIONAL]
        uAction.retriable(self._upgradeHelmPackages)(helms_to_update, groups_to_update)
        uLogging.info('Helm upgrade completed')


    def install(self, helms_to_update, repo_version):
        if not self.isHelmInstalled(): return
        uAction.retriable(self._setupK8sApi)()
        uAction.retriable(self._setupRepos)(repo_version)
        uAction.retriable(self._updateHelmRepo)()
        groups_to_install = [HelmGroup.FOUNDATION, HelmGroup.REQUIRED]
        uAction.retriable(self._upgradeHelmPackages)(helms_to_update, groups_to_install)
        uLogging.info('Helm install completed')


def clusterHealthPrecheck(helms_to_update):
    Helm().checkCapacityForUpgrade(helms_to_update)

def upgrade(helms_to_update, repo_version):
    Helm().upgrade(helms_to_update, repo_version)


def install(helms_to_update, repo_version, k8s_repo_url=None, k8s_docker_repo_host=None):
    Helm(k8s_repo_url, k8s_docker_repo_host).install(helms_to_update, repo_version)

