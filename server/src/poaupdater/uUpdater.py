from poaupdater import uAction, uBilling, uLogging, uPEM, uRoutines, uSlaveUpdater, uSysDB, uUtil, uDialog
import glob, os, shutil, sys

class DirectUpgradeState(object):

    def _getDirectoryName(self):
        return 'direct_upgrade'

    def _getOaUpdaterCommandFileName(self):
        return 'oa-updater-command.txt'

    def getDirectory(self):
        return self._directory

    def _directoryExists(self):
        return os.path.exists(self.getDirectory())

    def _createDirectory(self):
        uLogging.debug('Create directory: "%s"' % self.getDirectory())
        os.makedirs(self.getDirectory())

    def _initDirectory(self):
        if not self._directoryExists():
            self._createDirectory()

    def _getUdlFileName(self, udlFilePath):
        return os.path.basename(udlFilePath)

    def _getFilePath(self, filename):
        return os.path.join(self.getDirectory(), filename)

    def _getUdlFileNewPath(self, udlFilePath, buildName):
        newFilename = '%s_%s' % (buildName, self._getUdlFileName(udlFilePath))
        return self._getFilePath(newFilename)

    def _hasFile(self, filename):
        return os.path.exists(self._getFilePath(filename))

    def _writeToFile(self, filename, record):
        filePath = self._getFilePath(filename)
        f = open(filePath, 'w')
        try:
            uLogging.debug('Write to file "%s" record: "%s"' % (filePath, record))
            f.write(record)
        finally:
            f.close()

    def _readFromFile(self, filename):
        filePath = self._getFilePath(filename)
        if os.path.exists(filePath):
            f = open(filePath, 'r')
            try:
                record = f.read()
                uLogging.debug('Read from file "%s" record: "%s"' % (filePath, record))
                return record
            finally:
                f.close()
        else:
            errorMessage = 'File not found: %s' % filePath
            uLogging.err(errorMessage)
            raise Exception(errorMessage)

    def _removeFile(self, filename):
        filePath = self._getFilePath(filename)
        if os.path.exists(filePath):
            uLogging.debug('Remove file: "%s"' % filePath)
            os.remove(filePath)

    def __init__(self):
        self._directory = os.path.join(uPEM.getPemDirectory(), 'var', self._getDirectoryName())
        self._initDirectory()

    @staticmethod
    def init():
        DirectUpgradeState()

    def addUdlFile(self, udlFilePath, buildName):
        udlFileNewPath = self._getUdlFileNewPath(udlFilePath, buildName)
        uLogging.debug('Copy UDL file from: "%s" to: "%s"' % (udlFilePath, udlFileNewPath))
        shutil.copy2(udlFilePath, udlFileNewPath)

    def getUdlFiles(self):
        return glob.glob(os.path.join(self.getDirectory(), '*.udl2'))

    def empty(self):
        return not bool(self.getUdlFiles())

    def clear(self):
        for udlFile in self.getUdlFiles():
            uLogging.debug('Remove UDL file: "%s"' % udlFile)
            os.remove(udlFile)
        self._removeFile(self._getOaUpdaterCommandFileName())

    def hasOaUpdaterCommand(self):
        return self._hasFile(self._getOaUpdaterCommandFileName())

    def writeOaUpdaterCommand(self, command):
        self._writeToFile(self._getOaUpdaterCommandFileName(), command)

    def readOaUpdaterCommand(self):
        return self._readFromFile(self._getOaUpdaterCommandFileName())

class BaUpdater(object):

    def _getRootpath(self):
        return self._rootpath

    def _getConnection(self):
        return uSysDB.connect()

    def _importBillingComponentsInstaller(self):
        rootpath_bin = os.path.join(self._getRootpath(), 'bin')
        sys.path.append(rootpath_bin)
        global billing_components_installer
        import billing_components_installer

    def _getBillingHosts(self):
        return uBilling.get_billing_hosts()

    def _updateBillingPlatform(self):
        billing_components_installer.update_billing_platform()

    def _updateBillingServices(self):
        billing_components_installer.update_billing_services()

    def _updateBilling(self):
        self._updateBillingPlatform()
        self._updateBillingServices()

    def __init__(self, rootpath):
        self._rootpath = rootpath
        self._importBillingComponentsInstaller()

    def upgrade(self, upgrade_instructions, newest_packages):
        con = self._getConnection()
        billing_packages = []
        hosts_ids = self._getBillingHosts().values()
        uLogging.info('Upgrade packages on hosts: %s' % hosts_ids)
        for host_id in hosts_ids:
            billing_packages.extend(uRoutines.getPkgsToInstall(con, host_id, upgrade_instructions, newest_packages))
        if billing_packages:
            self._updateBilling()

    def getHostsWithAgent(self):
        billing_hosts = self._getBillingHosts().values()
        return [host for host in uPEM.get_hosts_with_agent() if host.host_id in billing_hosts]

    def upgradePaagentAndRepourl(self, binfo, config):
        self.upgradeAgentAndRepourl(binfo, config, self.getHostsWithAgent())

    def upgradeAgentAndRepourl(self, binfo, config, hosts_with_agent):
        uAction.retriable(uSlaveUpdater.upgrade_paagent_and_repourl)(binfo, config, hosts_with_agent)


class BaPlatformUpdater(BaUpdater):

    def _getBillingHosts(self):
        return uBilling.get_billing_platform_hosts()

    def _updateBilling(self):
        self._updateBillingPlatform()

    def __init__(self, rootpath):
        super(self.__class__, self).__init__(rootpath)


class BaServicesUpdater(BaUpdater):

    def _getBillingHosts(self):
        return uBilling.get_billing_service_hosts()

    def _updateBilling(self):
        self._updateBillingServices()

    def __init__(self, rootpath):
        super(self.__class__, self).__init__(rootpath)


class OaServicesUpdater(object):

    def getHostsWithAgent(self):
        hosts = [1]
        hosts.extend(uBilling.get_billing_hosts().values())
        return [host for host in uPEM.get_hosts_with_agent() if host.host_id not in hosts]

    def upgradePaagentAndRepourl(self, binfo, config):
        self.upgradeAgentAndRepourl(binfo, config, self.getHostsWithAgent())

    def upgradeAgentAndRepourl(self, binfo, config, hosts_with_agent):
        uAction.retriable(uSlaveUpdater.upgrade_paagent_and_repourl)(binfo, config, hosts_with_agent)


def getHostsToUpdate(binfo, hosts, upgrade_instructions, newest_packages):
    newAgentHosts = []
    newPackagesHosts = []
    if not hosts: return newAgentHosts, newPackagesHosts
    newAgent = uSlaveUpdater.is_need_to_update_paagent(binfo)
    con = uSysDB.connect()
    for host in hosts:
        if uRoutines.getPkgsToInstall(con, host.host_id, upgrade_instructions, newest_packages):
            newAgentHosts.append(host) # required to update repourl
            newPackagesHosts.append(host)
        elif newAgent:
            newAgentHosts.append(host)
    return newAgentHosts, newPackagesHosts


class OaCoreHaUpdater(object):

    def _init_ha_config(self, config):
        uLogging.debug("Attempting to import uHA module from %s...", self._u_dir)

        sys.path.insert(0, self._u_dir)
        try:
            import uHA
            uAction.progress.do("reading OA Core HA configuration")
            uHA.init(config)
            uAction.progress.done()
            self._ha = uHA
        finally:
            sys.path.remove(self._u_dir)

    def __init__(self, config, build_info):
        # where to import the latest uHA module from
        self._u_dir = None
        # the module itself
        self._ha = None

        if build_info.jboss_components.distribution:
            # JBoss will be re-installed, take uHA
            # module from distributive
            u_dir = build_info.jboss_components.distribution
            u_ha = os.path.join(u_dir, "uHA.py")
            if os.path.isfile(u_ha):
                self._u_dir = u_dir

        if not self._u_dir:
            # no JBoss distributive for upgrade, check if installed
            # OA has uHA module
            u_dir = os.path.join(config.rootpath, "u")
            u_ha = os.path.join(u_dir, "uHA.py")
            if os.path.isfile(u_ha):
                self._u_dir = u_dir

        if self._u_dir:
            uAction.retriable(self._init_ha_config)(config)
        else:
            uLogging.debug("No uHA module found")

    def precheck(self):
        if self._ha:
            self._ha.check_configuration()
        else:
            uLogging.debug("OA Core HA is not configured")

    def shutdown_extra_mn(self):
        if self._ha:
            uAction.progress.do("shutting down extra MN")
            uAction.retriable(self._ha.shutdown_extra_mn)()
            uAction.progress.done()

    def configure_mn(self):
        if self._ha:
            uAction.progress.do("re-configuring OA Core HA (OA MN, OA DB, OA additional MN)")
            uAction.retriable(self._ha.configure_mn)()
            uAction.progress.done()

    def configure_ui(self):
        if self._ha:
            uAction.progress.do("re-configuring OA Core HA (OA UI)")
            uAction.retriable(self._ha.configure_ui)(start_extra_mn=True)
            uAction.progress.done()


class BatchModeHandler(object):

    def __init__(self, config,opts):
        self.config = config
        dev_action_opts = '--dev-actions-run' in opts
        if config.batch and not dev_action_opts:
           uLogging.info("Setting batch mode.")
           uAction.retriable = self.mockRetriable
           uDialog.askYesNo = self.mockUser
        else:
           uLogging.info("Config.batch = %s , --dev-actions-run in opts = %s" % (config.batch , dev_action_opts))

    def mockUser(self,question=None, default=None):
        # consider 'yes' answer to every question in batch mode
        if default:
            uLogging.debug("Ignoring default value in batch mode. Value = %s" % default )
        uLogging.info(question)
        uLogging.info("Yes")
        return True

    def mockRetriable(self,fun, raise_on_ignore=False, allow_console=None):
        # just run it without retries
        def fn(*args, **kwargs):
            try:
                uLogging.debug("calling mocked retriable function %s" % fun )
                return fun(*args, **kwargs)
            except Exception, e:
                uLogging.err("Retriable raised error in batch mode: %s", e)
                raise
        return fn


class BssDbArtifacts(uUtil.TgzArtifacts):

    @staticmethod
    def _getBssDbArtifactsDirectoryName():
        return 'updater'

    @staticmethod
    def _getBssDbArtifactsFilenames():
        # Keep 'bss-db-migration-DB-MIGRATION.tgz' as first artifact in the list:
        return ['bss-db-migration-assembly.tgz', 'dbupdater.tgz']

    @staticmethod
    def _getBssDbArtifactsPath():
        return os.path.join(uPEM.getPemDirectory(), BssDbArtifacts._getBssDbArtifactsDirectoryName())

    def _getDbMigrationArtifact(self):
        return self.get()[0]

    def _getDbMigrationArtifactDistribPath(self, distribPath):
        return os.path.join(distribPath, 'db', 'bss', self._getDbMigrationArtifact().getFilename())

    def _copyDbMigrationArtifactFromDistrib(self, distribPath):
        shutil.copy2(self._getDbMigrationArtifactDistribPath(distribPath), self._getDbMigrationArtifact().getPath())

    def __init__(self):
        super(self.__class__, self).__init__(
            self._getBssDbArtifactsPath(),
            self._getBssDbArtifactsFilenames()
        )

    def install(self, distribPath):
        self._copyDbMigrationArtifactFromDistrib(distribPath)
        self.unpack()


def installBssDbArtifacts(distribPath):
    return BssDbArtifacts().install(distribPath)

