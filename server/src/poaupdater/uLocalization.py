from poaupdater import uBilling, uPackaging, uLogging, uPEM, uDialog
import os, subprocess

class Locale(object):
    namePrefix = 'prefix_'
    nameDelimiter = '.'
    def __parseId(self, name):
        return name.replace(self.namePrefix,'',1).split(self.nameDelimiter)[0]
    def __init__(self, name, ctype):
        self.__name = name
        self.__ctype = ctype
        self.__id = self.__parseId(name)
    def getName(self):
        return self.__name
    def getCtype(self):
        return self.__ctype
    def getId(self):
        return self.__id
    def install(self, hostId):
        if uPackaging.pkg_installed(hostId, (self.getCtype(), self.getName())):
            uLogging.info('Reinstalling locale: "%s" (host_id=%d)' % (self.getName(), hostId))
            uPackaging.reinstallPackageToHost(hostId, self.getName(), self.getCtype())
        else:
            uLogging.info('Installing locale: "%s" (host_id=%d)' % (self.getName(), hostId))
            uPackaging.installPackageToHostAPI(hostId, name = self.getName(), ctype = self.getCtype())
    def __str__(self):
        return self.getName()
    @classmethod
    def getAvailableLocales(cls, hostId):
        if not hostId: return {}
        locales = [cls(pkg[1], pkg[2]) for pkg in uPackaging.listAvailablePackages(hostId) if pkg[1].startswith(cls.namePrefix)]
        return dict((locale.getId(), locale) for locale in locales)
    @classmethod
    def getInstalledLocales(cls, hostId):
        if not hostId: return {}
        locales = [cls(pkg.name, pkg.ctype) for pkg in uPackaging.listInstalledPackagesOnHost(hostId) if pkg.name.startswith(cls.namePrefix)]
        return dict((locale.getId(), locale) for locale in locales)

class OaLocale(Locale):
    namePrefix = 'lp_'
    nameDelimiter = '_'
    def __init__(self, name, ctype):
        super(self.__class__, self).__init__(name, ctype)

class BaLocale(Locale):
    namePrefix = 'bm-locale-'
    nameDelimiter = '-'
    def __init__(self, name, ctype):
        super(self.__class__, self).__init__(name, ctype)

class CspLocales(object):

    @staticmethod
    def getPackage():
        return 'CSP-APS-Config-Deployment'

    @staticmethod
    def getDirectory():
        return os.path.join(uPEM.getPemDirectory(), 'CSP', 'o365-import')

    @staticmethod
    def getConfigurationScript():
        return os.path.join(CspLocales.getDirectory(), 'pba_upgrade_helper.py')

    @staticmethod
    def exists():
        foundCsp = len([pkg for pkg in uPackaging.listInstalledPackagesOnHost(1) if pkg.name == CspLocales.getPackage()]) > 0
        if not foundCsp:
            uLogging.debug('CSP package "%s" was not found.' % CspLocales.getPackage())
            return False
        if not os.path.isdir(CspLocales.getDirectory()):
            uLogging.err('CSP directory "%s" was not found.' % CspLocales.getDirectory())
            return False
        if not os.path.isfile(CspLocales.getConfigurationScript()):
            uLogging.err('CSP configuration script "%s" was not found.' % CspLocales.getConfigurationScript())
            return False
        return True

    @staticmethod
    def update(localesIds):
        if CspLocales.exists():
            uLogging.info('Updating CSP locales: %s' % localesIds)
            cspPath = CspLocales.getDirectory()
            out = subprocess.check_output('cd %s && (echo "import pba_upgrade_helper"; echo "pba_upgrade_helper.update_csp_locales(%s)") | python' % (cspPath, localesIds), shell=True)
            uLogging.debug(out)
        else:
            uLogging.debug('CSP locales was not found.')

class Locales(object):

    @staticmethod
    def getInstalledLocalesLimit():
        # excluding English
        return 8

    @staticmethod
    def __getOaHostId():
        return 1

    @staticmethod
    def __getBaHostId():
        baHost = uBilling.PBAConf
        try:
            return baHost.get_host_id()
        except:
            uLogging.debug('Component "%s" does not exist.' % baHost.name)
            return None

    @staticmethod
    def __configureBa(localesIds):
        uBilling.PBAConf.configure()
        uBilling.PBAConf.syncLocalesFromDB()
        CspLocales.update(localesIds)
        uBilling.PBAConf.stop()
        uBilling.PBAConf.start()
        uBilling.PBAConf.syncStores()

    @staticmethod
    def stripIds(localesIds):
        if localesIds is None:
            return None
        else:
            return [localeId.strip() for localeId in localesIds.split(',')]

    @staticmethod
    def getAvailableIds():
        oaHostId = Locales.__getOaHostId()
        baHostId = Locales.__getBaHostId()
        ids = set(OaLocale.getAvailableLocales(oaHostId))
        if baHostId:
           ids = ids & set(BaLocale.getAvailableLocales(baHostId))
        return sorted(list(ids))

    @staticmethod
    def getInstalledIds():
        oaHostId = Locales.__getOaHostId()
        baHostId = Locales.__getBaHostId()
        ids = set(OaLocale.getInstalledLocales(oaHostId))
        if baHostId:
           ids = ids & set(BaLocale.getInstalledLocales(baHostId))
        return sorted(list(ids))

    @staticmethod
    def getInstalledOaIds():
        oaHostId = Locales.__getOaHostId()
        return sorted(list(OaLocale.getInstalledLocales(oaHostId)))

    @staticmethod
    def getInstalledBaIds():
        baHostId = Locales.__getBaHostId()
        return sorted(list(BaLocale.getInstalledLocales(baHostId) if baHostId else []))

    @staticmethod
    def getIds(newLocalesIds, oaHostId, baHostId):
        englishLocale = set(['en'])
        newLocales = set([] if newLocalesIds is None else newLocalesIds)
        oaLocales = set() if oaHostId is None else englishLocale | set(OaLocale.getInstalledLocales(oaHostId).keys())
        baLocales = set() if baHostId is None else englishLocale | set(BaLocale.getInstalledLocales(baHostId).keys())
        return sorted(list(newLocales | oaLocales | baLocales))

    @staticmethod
    def checkLimit(newLocalesIds, oaHostId, baHostId):
        oldLocales = Locales.getIds(None, oaHostId, baHostId)
        newLocales = Locales.getIds(newLocalesIds, None, None)
        allLocales = Locales.getIds(newLocalesIds, oaHostId, baHostId)
        uLogging.info('%d locale(s) already installed %s' % (len(oldLocales), oldLocales))
        uLogging.info('%d locale(s) will be installed %s' % (len(newLocales), newLocales))
        uLogging.info('%d locale(s) will be in total %s' % (len(allLocales), allLocales))
        localesLimit = Locales.getInstalledLocalesLimit()
        if len(allLocales) > localesLimit:
            uLogging.err('Impossible to have in total more than %d locales (including English)' % localesLimit)
            raise Exception('Locales update was rejected: locales limit is reached (%d)' % localesLimit)

    @staticmethod
    def checkAvailability(newLocalesIds):
        unknownLocales = sorted(list(set(newLocalesIds) - set(Locales.getAvailableIds())))
        if len(unknownLocales) > 0:
            uLogging.err('Impossible to install unknown locales %s' % unknownLocales)
            raise Exception('Locales update was rejected: unknown locales %s' % unknownLocales)

    @staticmethod
    def install(localesIds, batchMode):
        try:
            oaHostId = Locales.__getOaHostId()
            baHostId = Locales.__getBaHostId()

            Locales.checkAvailability(localesIds)
            Locales.checkLimit(localesIds, oaHostId, baHostId)

            if baHostId:
                uLogging.info('Stores will be synchronized during locales update process.')
                uLogging.info('Billing services will be restarted during locales update process and may be unavailable for some time.')
                if not batchMode and not uDialog.askYesNo('Do you wish to continue?'):
                    uLogging.info('Locales update was rejected.')
                    return

            oaLocales = OaLocale.getAvailableLocales(oaHostId)
            baLocales = BaLocale.getAvailableLocales(baHostId)

            baNeedConfigure = False
            for localeId in localesIds:
                if localeId in oaLocales:
                    for hostId in uPEM.getAllUiHosts():
                        uiLocales = OaLocale.getAvailableLocales(hostId)
                        if localeId in uiLocales:
                            uiLocales[localeId].install(hostId)
                        else:
                            uLogging.err('OA locale "%s" was not found (hostId=%s)' % (localeId, hostId))
                else:
                    uLogging.err('OA locale "%s" was not found (hostId=%s)' % (localeId, oaHostId))
                    continue
                if not baHostId:
                    continue
                if localeId in baLocales:
                    baLocales[localeId].install(baHostId)
                    baNeedConfigure = True
                else:
                    uLogging.err('BA locale "%s" was not found (hostId=%s)' % (localeId, baHostId))
                    continue

            if baHostId and baNeedConfigure:
                Locales.__configureBa(localesIds)
        except Exception as e:
            uLogging.debug(e)

