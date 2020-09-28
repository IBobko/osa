from poaupdater import uLogging, uPEM, uConfig, uUtil, uSysDB, uAction, uHCL, openapi, PEMVersion, uPackaging, uConst
from urlparse import urlparse

import json
import pprint
import os.path
import re
from netaddr import IPNetwork

helm_version = 'v2.11.0'
helm_distr = 'helm-%s-linux-amd64.tar.gz' % helm_version
default_k8s_docker_repo_host = uConst.DEFAULT_K8S_DOCKER_REPO_HOST
default_helm_repo_prefix = uConst.DEFAULT_K8S_REPO_URL
default_helm_repo_username = uConst.DEFAULT_K8S_REPO_USERNAME
default_helm_repo_password = uConst.DEFAULT_K8S_REPO_PASSWORD
default_pod_networ_cidr = '10.244.0.0/16'
default_service_cidr = '10.96.0.0/12'

_long_options = [
    ('help', 'prints helm message'),
    ('check', 'check node before K8s deployment'),
    ('install', 'install simple K8s cluster in one-node configuration'),
    ('dry-run', 'simulate an install, do not perform any actions'),
    ('proxy=', 'use http proxy for K8s outbound communication'),
    ('repo=', 'chart repository url'),
    ('username=', 'chart repository username'),
    ('password=', 'chart repository password'),
    ('pod-network-cidr=', 'range of IP addresses for the pod network (default "%s")' % default_pod_networ_cidr),
    ('service-cidr=', ' range of IP address for service VIPs (default "%s")' % default_service_cidr),
]

def _log_cmd(msg):
    uLogging.debug(msg)
def _log_stdout(msg):
    uLogging.debug(msg)
def _log_stderr(msg):
    uLogging.debug(msg)

def retriable(fn):
    def action(*args, **kwargs):
        msg = [fn.__name__] + [str(x) for x in args] + ['%s=%s' % x for x in kwargs.iteritems()]
        uAction.progress.do(' '.join(msg).replace('%', '%%'))
        try:
            return uAction.retriable(fn)(*args, **kwargs)
        finally:
            uAction.progress.done()
    return action

def deep_get(dictionary, keys, default=None):
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)

def cpu_to_items(cpu_req):
    if cpu_req.endswith('m'):
        cpu_req = float(cpu_req.replace("m", "")) / 1000
    else:
        cpu_req = float(cpu_req)

    return cpu_req

def mem_to_bytes(mem_req):
    mem_suffixes = { 'G': 10**9, 'M': 10**6, 'K': 10**3, 'Gi': 2**30, 'Mi': 2**20, 'Ki': 2**10 } 
    for key in mem_suffixes:
        if mem_req.endswith(key):
            mem_req = mem_req.replace(key, '')
            mem_req = float(mem_req) * mem_suffixes[key]
            break

    return float(mem_req)

def get_nodes_allocated_resources():
    return uUtil.readCmd("kubectl describe node | grep Allocated -A 5 | grep -P 'cpu|memory' | awk '{print $3}' | sed -e 's/[^0-9]//g'").splitlines()

def get_nodes_capacity():
    return uUtil.readCmd("kubectl describe node | grep Capacity: -A 7 | grep -P 'cpu|memory' | awk '{print $2}'").splitlines()

class Repo(object):
    helm_repo_name = 'a8n'
    url_pattern = re.compile('(.*)/a8n-helm.*')
    yaml_pattern = re.compile('.*\s+(name|username|url|password):\s+(.*)')

    def __init__(self, prefix=default_helm_repo_prefix, username=default_helm_repo_username, password=default_helm_repo_password):
        self._upgradable_url = True
        self.prefix = prefix
        self.username = username
        self.password = password

    def __nonzero__(self):
        return bool(self.prefix)

    def is_upgradable_url(self):
        return self._upgradable_url

    def need_configure(self):
        return Repo.release() >= [7, 4]

    @staticmethod
    def version():
        return uPEM.get_major_version()

    @staticmethod
    def release():
        return map(int, Repo.version().split('.'))

    @staticmethod
    def release_name():
        return Repo.custom_name(Repo.version())

    def release_url(self):
        return self.custom_url(Repo.version())

    def helm_username_param(self):
        return ' --username=%s' % self.username if self.username else ''

    def helm_password_param(self):
        return ' --password=%s' % self.password if self.password else ''

    def helm_repo_add_cmd(self):
        return self.custom_helm_repo_add_cmd(Repo.version())

    def from_file(self, repo_file):
        self._upgradable_url = True
        params = {}
        with open(repo_file) as f:
            for line in f:
                if line[0:1] == '-':
                    if params.get('name') == Repo.helm_repo_name:
                        break
                    else:
                        params.clear()
                g = Repo.yaml_pattern.match(line)
                if g:
                    params[g.group(1)] = g.group(2)
        if params.get('name') == Repo.helm_repo_name:
            if 'username' in params:
                self.username = params['username']
            if 'password' in params:
                self.password = params['password']
            if 'url' in params:
                m = Repo.url_pattern.match(params['url'])
                if m:
                    self.prefix = m.group(1)
                else:
                    self._upgradable_url = False

    @staticmethod
    def custom_name(version):
        return 'a8n-helm-' + version

    def custom_url(self, version):
        return '%s/%s/' % (self.prefix, Repo.custom_name(version))

    def custom_helm_repo_add_cmd(self, version):
        return self.custom_url(version) + self.helm_username_param() + self.helm_password_param()

    @staticmethod
    def custom_name(version):
        return 'a8n-helm-' + version

    def custom_url(self, version):
        return '%s/%s/' % (self.prefix, Repo.custom_name(version))

    def custom_helm_repo_add_cmd(self, version):
        return self.custom_url(version) + self.helm_username_param() + self.helm_password_param()


class HCL(object):
    def __init__(self, host_id, dry_run=False):
        self.host_id = host_id
        self.dry_run = dry_run

    def __str__(self):
        return '[#%s]' % self.host_id

    def request(self):
        return uHCL.Request(self.host_id, 'root', 'root')

    @retriable
    def run(self, *args, **kwargs):
        _log_cmd(' '.join(args))
        r = self.request()

        kwargs_def = dict({'stdout': 'stdout', 'stderr': 'stderr'}, **kwargs)
        r.command(*args, **kwargs_def)

        for e in r._Request__perform.getElementsByTagName('EXEC'):
            env_elem = r._Request__document.createElement('ENV_VAR')
            env_elem.setAttribute('name', 'HOME')
            env_elem.setAttribute('value', '/root')
            e.appendChild(env_elem)

        res = r.perform() if not self.dry_run else {kwargs_def['stdout']: '', kwargs_def['stderr']: ''}
        if 'stdout' in res and res['stdout']:
            _log_stdout(res['stdout'])
        if 'stderr' in res and res['stderr']:
            _log_stderr(res['stderr'])
        return res

    @retriable
    def transfer(self, src, path_from, path_to):
        _log_cmd('Transfer %s from %s' % (path_from, src))
        r = self.request()
        r.transfer(str(src.host_id), path_from, path_to)
        if not self.dry_run:
            r.perform()


class K8sHostNotFound(Exception):
    def __init__(self):
        Exception.__init__(self, "Can't find K8s host. Please assign attribute %s to the host" % K8sHost.attribute_marker)


class NetworkNotFound(Exception):
    def __init__(self, host_id, backnet_ip):
        Exception.__init__(self, "Can't detect network config in DB for host #%s ip %s" % (host_id, backnet_ip))


class K8s(object):

    def __init__(self, host_id=1, proxy=None):
        self.host_id = host_id
        self.master_ip = uPEM.getHostCommunicationIP(self.host_id)
        self.proxy = K8sHost.detect_proxy() if proxy is None else proxy

    def _get_master_location(self):
        command = ['kubectl', 'config', 'view', '--minify=true', '--output=json']
        url = json.loads(uUtil.readCmd(command)).get('clusters', [{}])[0].get('cluster', {}).get('server', '')
        return urlparse(url).hostname or ''

    @staticmethod
    def get_helm_repo():
        repo = Repo()
        repo_file = os.path.join('/root', '.helm', 'repository', 'repositories.yaml')
        if os.path.isfile(repo_file):
            repo.from_file(repo_file)
        return repo

    @staticmethod
    def detect_proxy():
        privoxy = uPackaging.listInstalledPackages('PrivacyProxy', 'other')
        if not privoxy:
            return None
        privoxy_component = privoxy[0].component_id
        proxy_ip, proxy_port = None, None
        con = uSysDB.connect()
        cur = con.cursor()
        cur.execute("select name, value from v_props where name in ('privoxy.backnet_ip', 'privoxy.port') and component_id=%s", privoxy_component)
        for name, value in cur.fetchall():
            if name == 'privoxy.backnet_ip':
                proxy_ip = str(value)
            elif name == 'privoxy.port':
                proxy_port = str(value)

        if proxy_ip and proxy_port:
            return 'http://%s:%s' % (proxy_ip, proxy_port)
        return None

    def get_https_proxy(self):
        return 'https_proxy=%s ' % self.proxy if self.proxy else ''

    def get_http_proxy(self):
        return 'http_proxy=%s ' % self.proxy if self.proxy else ''

    def get_full_proxy(self):
        return self.get_https_proxy() + self.get_http_proxy()

    def get_helm_cmd(self):
        proxy = '%sno_proxy=%s ' % (self.get_https_proxy(), self._get_master_location()) if self.proxy else ''
        return '%s/usr/local/bin/helm' % proxy

    def get_helm_client_install_cmds(self, tmp_dir):
        cmds = []
        tmp_dist = '%s/%s' % (tmp_dir, helm_distr)
        cmds.append('%swget https://storage.googleapis.com/kubernetes-helm/%s -q -O %s' % (self.get_https_proxy(), helm_distr, tmp_dist))
        cmds.append('tar xf %s -C %s' % (tmp_dist, tmp_dir))
        cmds.append('cp %s/linux-amd64/helm /usr/local/bin/helm' % tmp_dir)
        cmds.append('rm -rf %s' % tmp_dir)
        return cmds

    def get_helm_repo_add_cmd(self, repo):
        return self.get_custom_helm_repo_add_cmd(repo, Repo.version())

    def get_custom_helm_repo_add_cmd(self, repo, version):
        return '%s repo add %s %s' % (self.get_helm_cmd(), Repo.helm_repo_name, repo.custom_helm_repo_add_cmd(version))

    def get_image_pull_secrets_patch_cmd(self):
        return 'kubectl patch serviceaccount default -p \'{"imagePullSecrets": [{"name": "a8n-docker-registry"}]}\''

    @staticmethod
    def getReadyNodes():
        return uUtil.readCmd("kubectl get node --no-headers  | grep Ready | awk '{print $1}'")

    @staticmethod
    def getNodesMemoryCapacity(node):
        mem=[]
        for node in getReadyNodes():
            mem.add(getNodeMemoryCapacity(node))
        return mem

    @staticmethod
    def getNodesCPUCapacity(node):
        mem=[]
        for node in getReadyNodes():
            mem.add(getNodeCPUCapacity(node))
        return mem

    @staticmethod
    def getChartDeployments(chart_name):
        output = uUtil.readCmd("kubectl get deployment --no-headers -l release=%s -o json" % chart_name)
        if not output: output = '{}'
        return json.loads(output)

    @staticmethod
    def getChartStatefulSet(chart_name):
        output = uUtil.readCmd("kubectl get StatefulSet --no-headers -l release=%s -o json" % chart_name)
        if not output: output = '{}'
        return json.loads(output)

    @staticmethod
    def getUpgradeResourcePerItem(info, strategy_path):
        if not info:
            return [0, 0]

        strategyType = deep_get(info, strategy_path+'.type')
        if strategyType and strategyType != 'RollingUpdate':
            return [0, 0]

        containers = deep_get(info, 'spec.template.spec.containers')
        if not containers:
            return [0, 0]

        max_unavailable = deep_get(info, 'spec.strategy.rollingUpdate.maxUnavailable')
        replicas = deep_get(info, 'spec.replicas')
        if str(max_unavailable).endswith('%'):
            mu = int(max_unavailable.replace('%', ""))
            allowed_unavailable = int(int(replicas) * mu / 100)
        else:
            allowed_unavailable = int(max_unavailable)
        if allowed_unavailable >= 1:
            # if one pod can be deleted, then we don't need extra resources: new pods will be created one by one
            return [0, 0]
        # else non of existing pods can be removed. So, we need space at least for one extra pod at a time

        cpu = mem = 0.0
        # assume that no microservice will require Ti mem, we will support Gi and below
        for container in containers:
            cpu_req = deep_get(container, 'resources.requests.cpu')
            if cpu_req:
                cpu = cpu + cpu_to_items(cpu_req)

            mem_req = deep_get(container, 'resources.requests.memory')
            if mem_req:
                mem = mem + mem_to_bytes(mem_req)

        return [cpu, mem]

    @staticmethod
    def getUpgradeResourceRequiment(chart_name):
        info = K8s.getChartDeployments(chart_name)
        strategy_path='spec.strategy'
        if not info.get('items') or not len(info.get('items')):
            info = K8s.getChartStatefulSet(chart_name)
            strategy_path='spec.updateStrategy'

        if not info.get('items') or not len(info.get('items')):
            return [0, 0]

        result = [0, 0]
        for item in info.get('items'):
            result = map(lambda x,y:max(x,y), result, K8s.getUpgradeResourcePerItem(item, strategy_path))

        return result

    @staticmethod
    def getNodesAvailableResources():
        nodesCapacity = []
        allocated = get_nodes_allocated_resources()
        capacity = get_nodes_capacity()
        max=0
        for i in range(1,len(capacity),2):
            cpu_allocated_percent = allocated[i-1]
            mem_allocated_percent = allocated[i]
            cpu_capacity = cpu_to_items(capacity[i-1])
            mem_capacity = mem_to_bytes(capacity[i])
            
            cpu_available = cpu_capacity - cpu_capacity * int(cpu_allocated_percent) / 100
            mem_available = mem_capacity - mem_capacity * int(mem_allocated_percent) / 100
            nodesCapacity.append([cpu_available, mem_available])

        return nodesCapacity

    @staticmethod
    def getPendingPods():
        return uUtil.readCmd("kubectl get pod | grep Pending | awk '{print $1}'")


class K8sHost(K8s):
    attribute_marker = 'K8s'

    def __init__(self, host_id, proxy=None, dry_run=False):
        if not host_id:
            raise K8sHostNotFound()
        super(self.__class__, self).__init__(host_id, proxy)
        self.hcl = HCL(self.host_id, dry_run)
        self.mn_hcl = HCL(1, dry_run)
        self.backnet = K8sHost.get_backnet_from_db(self.host_id, self.master_ip)

    def set_network(self, pod_network_cidr, service_cidr):
        self.pod_network = IPNetwork(pod_network_cidr)
        self.service_network = IPNetwork(service_cidr)

    @staticmethod
    def get_backnet_from_db(host_id, backnet_ip):
        con = uSysDB.connect()
        cur = con.cursor()
        cur.execute("select ip_address::inet & netmask::inet, netmask::inet from configured_ips where ip_address::inet=%s::inet and host_id = %s", backnet_ip, host_id)
        rec = cur.fetchone()
        if not rec:
            raise NetworkNotFound(host_id, backnet_ip)
        return IPNetwork(rec[0] + '/' + rec[1])

    @staticmethod
    def detectNodeInDB(con):
        cur = con.cursor()
        cur.execute('select host_id from host_attributes where host_attribute=%s', K8sHost.attribute_marker)
        rec = cur.fetchone()
        if not rec:
            return None
        return rec[0]

    def __str__(self):
        return 'K8s Host [%s]' % self.host_id

    def run(self, *args, **kwargs):
        return self.hcl.run(*args, **kwargs)

    def check(self):
        return True

    def is_oa_has_k8s_api(self):
        api = openapi.OpenAPI()
        try:
            api.pem.getSystemProperty(account_id=1, name='kubernetes_api')
        except openapi.OpenAPIError:
            return False
        return True

    def install(self, repo):
        self.deploy_master()
        self.setup_mn(repo)
        self.setup_oa()
        uLogging.info('Kubernetes is successfully registered')

    def deploy_master(self):
        self.install_docker()
        self.install_k8s()
        self.init_k8s()
        self.init_kubectl()
        self.get_k8s_status()
        self.init_k8s_network()
        self.get_k8s_status()

    def setup_mn(self, repo):
        self.setup_mn_k8s()
        self.install_helm()
        self.setup_mn_dns()
        self.setup_mn_route()

    def install_docker(self):
        self.run('swapoff -a')
        self.run("sed -i '/ swap / s/^/#/' /etc/fstab")
        self.run('%syum install -y -q docker' % self.get_http_proxy())
        self.run('systemctl enable docker')
        self.run('echo $\'net.bridge.bridge-nf-call-ip6tables = 1\\nnet.bridge.bridge-nf-call-iptables = 1\' > /etc/sysctl.d/k8s.conf')
        self.run('sysctl --system')
        self.run('mkdir -p /var/log/journal')
        if self.proxy:
            self.run('mkdir -p /etc/systemd/system/docker.service.d')
            self.run('echo $\'[Service]\\nEnvironment="HTTP_PROXY=%s" "HTTPS_PROXY=%s"\' > /etc/systemd/system/docker.service.d/http-proxy.conf' % (self.proxy, self.proxy))
            self.run('systemctl daemon-reload')
        self.run('systemctl restart docker')
        self.run('docker info')

    def install_k8s(self):
        self.run('echo $\'[kubernetes]\\nname=Kubernetes\\nbaseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64\\nenabled=1\\ngpgcheck=1\\nrepo_gpgcheck=1\\ngpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg\' > /etc/yum.repos.d/kubernetes.repo')
        self.run('setenforce 0', valid_exit_codes=[0, 1])
        self.run('%syum install -y -q kubelet-1.10.5 kubeadm-1.10.5 kubectl-1.10.5' % self.get_full_proxy())
        self.run('systemctl enable kubelet')
        self.run('systemctl start kubelet')

    def init_k8s(self):
        init_cmd = 'kubeadm init --pod-network-cidr=%s --service-cidr=%s --apiserver-advertise-address=%s' % (self.pod_network, self.service_network, self.master_ip)
        if self.proxy:
            init_cmd = 'NO_PROXY="%s,%s,%s" HTTPS_PROXY=%s HTTP_PROXY=%s %s' % (self.backnet, self.pod_network, self.service_network, self.proxy, self.proxy, init_cmd)
        self.run(init_cmd)

    def init_kubectl(self):
        self.run('mkdir -p /root/.kube')
        self.run('cp -i /etc/kubernetes/admin.conf /root/.kube/config')
        self.run('chown root:root /root/.kube/config')

    def init_k8s_network(self):
        self.run('%swget https://raw.githubusercontent.com/cloudnativelabs/kube-router/master/daemonset/kubeadm-kuberouter.yaml -q -O /tmp/kubeadm-kuberouter.yaml' % self.get_https_proxy())
        self.run('kubectl apply -f /tmp/kubeadm-kuberouter.yaml')
        self.run('kubectl rollout status deployment/kube-dns -n kube-system')

    def install_helm(self):
        self.mn_hcl.run('kubectl taint nodes --all node-role.kubernetes.io/master-')
        tmp_dir = self.mn_hcl.run('mktemp -dt helm-XXXXXX', stdout='tmp_dir')['tmp_dir'].strip() or '/tmp/helm'
        map(self.mn_hcl.run, self.get_helm_client_install_cmds(tmp_dir))
        self.mn_hcl.run('%s init' % self.get_helm_cmd())
        self.mn_hcl.run('kubectl create serviceaccount --namespace kube-system tiller')
        self.mn_hcl.run('kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller')
        self.mn_hcl.run('kubectl patch deploy --namespace kube-system tiller-deploy -p \'{"spec":{"template":{"spec":{"serviceAccount":"tiller","automountServiceAccountToken":true}}}}\'')
        self.mn_hcl.run('kubectl rollout status deployment/tiller-deploy -n kube-system')

    def setup_repo(self, repo):
        self.mn_hcl.run(self.get_helm_repo_add_cmd(repo))
        self.mn_hcl.run('%s del a8n-repo-config --purge' % self.get_helm_cmd(), valid_exit_codes=[0, 1])
        self.mn_hcl.run('kubectl delete secret a8n-docker-registry --ignore-not-found=true')
        self.mn_hcl.run('%s install -n a8n-repo-config a8n/repo-config --wait' % self.get_helm_cmd())
        cur_config = self.mn_hcl.run("kubectl get serviceaccount default -o=jsonpath='{.imagePullSecrets[*].name}'", stdout='config')['config']
        if cur_config != 'a8n-docker-registry':
            self.mn_hcl.run(self.get_image_pull_secrets_patch_cmd())

    def get_k8s_status(self):
        self.run('kubectl get pods -n kube-system')

    def setup_mn_k8s(self):
        self.mn_hcl.run('echo $\'[kubernetes]\\nname=Kubernetes\\nbaseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64\\nenabled=1\\ngpgcheck=1\\nrepo_gpgcheck=1\\ngpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg\' > /etc/yum.repos.d/kubernetes.repo')
        self.mn_hcl.run('%syum install -y -q kubectl-1.10.5' % self.get_full_proxy())
        self.mn_hcl.run('mkdir -p /root/.kube')
        self.mn_hcl.transfer(self.hcl, '/root/.kube/config', '/root/.kube')
        self.mn_hcl.run('chown root:root /root/.kube/config')

    def setup_mn_dns(self):
        dns = self.mn_hcl.run("kubectl get service kube-dns -n kube-system -o jsonpath='{.spec.clusterIP}'", stdout='dns')['dns']
        self.mn_hcl.run("sed -i \"1s/^/nameserver %s\\n/\" /etc/resolv.conf" % dns)
        self.mn_hcl.run("if grep -P '^search' {resolve}; then sed -i 's/^search.*/& {cluster}/' {resolve}; else sed -i '1s/^/search {cluster}\\n/' {resolve}; fi".format(resolve='/etc/resolv.conf', cluster='default.svc.cluster.local'))

    def setup_mn_route(self):
        self.mn_hcl.run('ip route add %s via %s' % (self.service_network, self.master_ip))

    def get_https_proxy(self):
        return 'https_proxy=%s ' % self.proxy if self.proxy else ''

    def get_http_proxy(self):
        return 'http_proxy=%s ' % self.proxy if self.proxy else ''

    def get_full_proxy(self):
        return self.get_https_proxy() + self.get_http_proxy()

    @retriable
    def setSystemProperties(self, props):
        api = openapi.OpenAPI()
        for name, value in props.iteritems():
            api.pem.setSystemProperty(account_id=1, name=name, str_value=value)

    def setup_skeleton(self):
        kubernetes_api = self.mn_hcl.run('kubectl config view -o jsonpath="{.clusters[*].cluster.server}"', stdout='apiserver')['apiserver']
        kubernetes_token = self.mn_hcl.run("kubectl get secret -n kube-system $(kubectl get secrets -n kube-system | grep tiller | cut -f1 -d ' ') -o jsonpath={.data.token} | base64 -d", stdout='token')['token']
        kubernetes_docker_repository_host = self.mn_hcl.run("%s inspect a8n/repo-config | grep server | cut -f2 -d ' '" % self.get_helm_cmd(), stdout='docker')['docker']

        if not self.mn_hcl.dry_run:
            self.setSystemProperties({'kubernetes_api': kubernetes_api,
                                      'kubernetes_token': kubernetes_token,
                                      'kubernetes_docker_repository_host': kubernetes_docker_repository_host})

        self.mn_hcl.transfer(self.hcl, '/etc/kubernetes/pki/apiserver.crt', '/usr/local/pem/kubernetes/certs')
        self.mn_hcl.run('mv /usr/local/pem/kubernetes/certs/apiserver.crt /usr/local/pem/kubernetes/certs/kubernetesApi.pem')
        self.mn_hcl.run('chown jboss:jboss /usr/local/pem/kubernetes/certs/kubernetesApi.pem')
        self.mn_hcl.run('chmod 0400 /usr/local/pem/kubernetes/certs/kubernetesApi.pem')

    def setup_oa(self):
        repo = K8sHost.get_helm_repo()
        if repo.need_configure():
            self.setup_repo(repo)

        if self.is_oa_has_k8s_api():
            self.setup_skeleton()

def _init(options):
    uLogging.init2(log_file='/var/log/pa/k8s.install.log', log_file_rotation=False, verbose=False)

    class PrintLogger(object):
        def __init__(self):
            self.terminal = sys.stdout

        def write(self, message):
            self.terminal.write(message)
            uLogging.debug(message)

        def flush(self):
            self.terminal.flush()

    sys.stdout = PrintLogger()

    uLogging.debug("Platform version is {0}".format(uPEM.get_major_version()))
    uLogging.debug("Command line %s " % (sys.argv))

    global _log_cmd, _log_stdout, _log_stderr

    def _log_cmd(msg):
        uLogging.info('\x1b[32m%s\x1b[0m' % msg)

    def _log_stdout(msg):
        uLogging.info(msg)

    def _log_stderr(msg):
        uLogging.info('\x1b[1m%s\x1b[0m', msg)

    global config
    config = uConfig.Config()
    openapi.initFromEnv(config)

    def use_option(key, attr, default=None, empty=True):
        if key in options:
            value = options[key]
            if value == "":
                value = empty
            setattr(config, attr, value)
        else:
            setattr(config, attr, default)

    use_option('--check', 'check')
    use_option('--install', 'install')
    use_option('--proxy', 'proxy', empty='')
    use_option('--dry-run', 'dry_run', False)
    use_option('--repo', 'prefix', default_helm_repo_prefix, empty='')
    use_option('--username', 'username', default_helm_repo_username, empty='')
    use_option('--password', 'password', default_helm_repo_password, empty='')
    use_option('--pod-network-cidr', 'pod_network_cidr', default_pod_networ_cidr)
    use_option('--service-cidr', 'service_cidr', default_service_cidr)

    uLogging.debug('Recognized config: \n' + pprint.pformat(uUtil.stipPasswords(vars(config))))

    uSysDB.init(config)

    k8s_host = K8sHost(host_id=K8sHost.detectNodeInDB(uSysDB.connect()), proxy=config.proxy, dry_run=config.dry_run)
    k8s_host.set_network(pod_network_cidr=config.pod_network_cidr, service_cidr=config.service_cidr)

    repo = Repo(prefix=config.prefix, username=config.username, password=config.password)

    return (k8s_host, repo)

def _usage():
    cmd = 'python -m poaupdater.uK8s'
    return [
        'Usage 1: %s --check ' % cmd,
        '\tto check a node marked by attribute "K8s" is ready for K8s deployment',
        '',
        'Usage 2: %s --install' % cmd,
        '\tto install simple K8s cluster in one-node configuration on a node marked by attribute "K8s"',
        '',
        ''] + ['\t--%s - %s' % opt for opt in _long_options]

def _print_usage():
    print '\n'.join(_usage())

def _save_traceback():
    import traceback
    uLogging.debug(str(sys.exc_info()))
    uLogging.debug(traceback.format_exc())

def _main(node, repo):
    if config.check:
        node.check()
    if config.install:
        if node.check():
            node.install(repo)


if __name__ == '__main__':
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')

    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], '', dict(_long_options).keys())
        opts = dict(opts)
    except getopt.GetoptError, err:
        print str(err)
        _print_usage()
        sys.exit(2)
    if opts and '--help' in opts:
        _print_usage()
        sys.exit(0)

    try:
        k8s_node, repo = _init(opts)
        _main(k8s_node, repo)
    except KeyboardInterrupt:
        _save_traceback()
        uLogging.debug("Keybord interrupted")
        sys.exit(3)
    except Exception, e:
        uLogging.err("%s", e)
        _save_traceback()

        if uLogging.logfile:
            uLogging.info("See additional info at %s" % uLogging.logfile.name)

        exit(1)
