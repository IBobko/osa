import os

class Const(object):

    @staticmethod
    def getWinPlatform():
        return 'win32'

    @staticmethod
    def isWinPlatform(sysPlatform):
        return sysPlatform == Const.getWinPlatform()

    @staticmethod
    def isWindows():
        import sys
        return Const.isWinPlatform(sys.platform)

    @staticmethod
    def isLinux():
        return not Const.isWindows()

    @staticmethod
    def getOsaWinPlatform():
        return 'Win32'

    @staticmethod
    def isOsaWinPlatform(osaPlatform):
        return osaPlatform == Const.getOsaWinPlatform()

    @staticmethod
    def getDistribWinDir():
        return 'win32'

    @staticmethod
    def getDistribLinDir():
        return 'RHEL'

    @staticmethod
    def getMinRhelVersion():
        """ Returns minimal supported RHEL (CentOS) version as tuple: (major, minor)
        """
        return (7, 4)

    @staticmethod
    def getMinRhelMajorVersion():
        return Const.getMinRhelVersion()[0]

    @staticmethod
    def getMinRhelMinorVersion():
        return Const.getMinRhelVersion()[1]

    @staticmethod
    def getMinSupportedLinux():
        return 'RHEL (CentOS) %s' % '.'.join(map(str, Const.getMinRhelVersion()))

    @staticmethod
    def getTarballsDir():
        return os.path.join('install', 'tarballs')

    @staticmethod
    def getCoreRpmsDir():
        return os.path.join(Const.getTarballsDir(), 'corerpms')

    @staticmethod
    def getCoreExesDir():
        return os.path.join(Const.getTarballsDir(), 'coreexes')


class HelmGroup(object):
    FOUNDATION = 'foundation'
    REQUIRED = 'required'
    OPTIONAL = 'optional'


class Modules:
    PLATFORM = 'Platform'
    APS = 'APS'
    PACI = 'PACI'
    BILLING = 'PBA'
    SHM = 'SHM'
    BCM = 'BCM'
    CSP = 'CSP'
    AZURE = 'Azure'
    SAMPLE_APPS = "Sample Applications"

    PBA = 'PBA'     # 3-N billing roles
    PBA_INTEGRATION = 'PBAIntegration'    # enabling 'Billling' button in PCP for 3-Node billing set

    CORE_MODULES = (PLATFORM, APS)
    ESSENTIALS_MODULES = (BILLING, PBA_INTEGRATION, PACI, SHM, BCM, CSP, AZURE)

ALLOW_SEND_STATISTICS_SYS_PROP = 'allow.send.statistics'
ALLOW_SEND_STATISTICS = True

DEFAULT_K8S_DOCKER_REPO_HOST = 'odindevops-a8n-docker.jfrog.io'
DEFAULT_K8S_REPO_URL = 'https://odindevops.jfrog.io/odindevops'
DEFAULT_K8S_REPO_USERNAME = 'operations'
DEFAULT_K8S_REPO_PASSWORD = '99bwy-TnLX4u'

__all__ = ['HelmGroup']

