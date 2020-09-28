import sys, os, socket, subprocess, getpass, pwd, logging, cStringIO, re, time, datetime
import uPgSQL, uUtil, uConfig, uSysDB, uPEM, uLogging, uLinux, uHCL, uBilling
import ConfigParser
from distutils.version import LooseVersion

global uUtil
PostgreSQLCmd = """ su - postgres -c "psql --port=%d -t -P format=unaligned -c \\"%s\\"" """

PG_SLAVE_END_RECOVERY_TIMEOUT_SECONDS = 600
DEFAULT_PG_PORT = 5432
PGHA_ACTIVE_CONF_PATH = "/usr/local/pem/etc/pgha.conf"
PG_CERT_VERIFY_KB_URL = "https://kb.cloudblue.com/en/131027"
PG_CERT_THRESHOLD_VALID_PERIOD_YEARS = 5

class PghaSettings:
    COMMON_SECTION_NAME = "common"

    def __init__(self, pgha_conf_path):
        self.isHa = False
        self.vip_1 = ""
        self.vip_2 = ""
        self.monitorAccount = ""
        self.monitorAccountPasswd = ""
        self.haBackendPort = 15432 # default
        self.aDbNode = ""
        self.bDbNode = ""

        if os.path.exists(pgha_conf_path):
            config = ConfigParser.ConfigParser()
            config.read(pgha_conf_path)

            self.isHa = config.has_option(PghaSettings.COMMON_SECTION_NAME, "IS_PGHA") and config.get(PghaSettings.COMMON_SECTION_NAME, "IS_PGHA").strip() == "1"
            self.vip_1 = config.get(PghaSettings.COMMON_SECTION_NAME, "PGHA_VIP").strip()
            self.vip_2 = config.get(PghaSettings.COMMON_SECTION_NAME,  "PGHA_VIP_2").strip()
            self.monitorAccount = config.get(PghaSettings.COMMON_SECTION_NAME,  "PG_MONITOR_ACCOUNT").strip()
            self.monitorAccountPasswd = config.get(PghaSettings.COMMON_SECTION_NAME, "PG_MONITOR_ACCOUNT_PASSWORD")
            self.haBackendPort = int(config.get(PghaSettings.COMMON_SECTION_NAME, "PG_BACKEND_PORT").strip())
            self.aDbNode = config.get(PghaSettings.COMMON_SECTION_NAME, "A_DB_NODE")
            self.bDbNode = config.get(PghaSettings.COMMON_SECTION_NAME, "B_DB_NODE")

def getPortPostgresIsListeningOn(run, pgPort = DEFAULT_PG_PORT):
    return run(PostgreSQLCmd % (pgPort, "SHOW port"))

def getWalKeepSegments(run, pgPort = DEFAULT_PG_PORT):
    return run(PostgreSQLCmd % (pgPort, "SELECT setting FROM pg_settings WHERE name = 'wal_keep_segments'"))

def getRecoveryConf(run, dataDir):
    return run("cat \"%s/recovery.conf\" 2> /dev/null" % dataDir)

def ipAddrToUserUniqPostfix(ipAddr):
    return "_"+ipAddr.replace(".", "_")

def listPgDatabases(run, pgPort = DEFAULT_PG_PORT):
    rv = run(PostgreSQLCmd % (pgPort, "SELECT datname FROM pg_database"))
    return rv.split('\n')

def checkHostPermittedToBeReplicaOfDB(run, hostName):
    authFile = "/root/auth_hosts"
    authFileBody = run(""" cat "%s" 2> /dev/null || echo -n """ % (authFile,))
    try:
        if not (hostName in authFileBody.splitlines()):
            raise Exception("Host is not authorized! Please add %s to %s file on master DB host." % (hostName, authFile))
    except IOError:
        raise Exception("Please put replicas hostnames into %s file on master DB host." % authFile)

def verifyPostgresCertificate(pgsqlOnMaster):
    uLogging.info("Make sure PostgreSQL server.crt satisfies the installation requirements according to the KB '%s'" % PG_CERT_VERIFY_KB_URL)

    serverCrtPath = pgsqlOnMaster.get_data_dir() + "/server.crt"
    runOnMaster = pgsqlOnMaster.get_commander()
    # make sure certificate exists
    try:
        checkExists = runOnMaster("[ -e '%s' ] && echo 'OK'" % serverCrtPath)
        if checkExists.strip() != 'OK':
            raise Exception("Certificate '%s' not found" % serverCrtPath)
    except Exception, ex:
        uLogging.err(ex.message)
        exceptionMsg = "Failed to validate existence of '%s' with error '%s'. Please refer to the KB %s" % (serverCrtPath, ex.message, PG_CERT_VERIFY_KB_URL)
        uLogging.warn("\n%s\n%s\n%s" %( "*" * 150,  exceptionMsg, "*" * 150))
        raise Exception(exceptionMsg)

    uLogging.info("Validate expiration date of the certificate '%s'" % serverCrtPath)
    # request certificate expiration date
    certExpireDateStr = runOnMaster("date --date=\"$(openssl x509 -in %s -noout -enddate | cut -d= -f 2)\" --iso-8601" % serverCrtPath).strip()

    # request PgSQL server's date
    masterServerDateStr = runOnMaster("date --iso-8601").strip()

    uLogging.info("The expiration date of master PostgreSQL certificate '%s', master server date '%s'" % (certExpireDateStr, masterServerDateStr))

    pgsqlCertExpireDate = datetime.datetime.strptime(certExpireDateStr, "%Y-%m-%d")
    masterServerDate = datetime.datetime.strptime(masterServerDateStr, "%Y-%m-%d")

    if pgsqlCertExpireDate < masterServerDate:
        exceptionMsg = """The PostgreSQL certificate '%s' is expired. For additional information please refer to the KB %s""" % \
                       (serverCrtPath, PG_CERT_VERIFY_KB_URL)
        uLogging.warn("\n%s\n%s\n%s" %( "*" * 150,  exceptionMsg, "*" * 150))
        raise Exception(exceptionMsg)

    timeDiff = pgsqlCertExpireDate - masterServerDate
    certificateValid = timeDiff.days >= 365 * PG_CERT_THRESHOLD_VALID_PERIOD_YEARS # raw estimation because of 365 days per year

    if not certificateValid:
        exceptionMsg = """The validity of the certificate '%s' expires in less than %d years. \
        The certificate's expiration date must be minimum %d years. For additional information please refer to the KB %s""" % \
                        (serverCrtPath, PG_CERT_THRESHOLD_VALID_PERIOD_YEARS, PG_CERT_THRESHOLD_VALID_PERIOD_YEARS, PG_CERT_VERIFY_KB_URL)
        uLogging.warn("\n%s\n%s\n%s" %( "*" * 150,  exceptionMsg, "*" * 150))
        raise Exception(exceptionMsg)

    uLogging.info("Certificate expiration date is successfully validated")

def getPghaSettings():
    pghaSettings = PghaSettings(PGHA_ACTIVE_CONF_PATH)

    return pghaSettings

def forceHaMasterSyncConf(run):
    uLogging.info("Force Master DB node to sync PostgreSQL configuration files")
    try:
        run("""/usr/local/pem/bin/pgha/pghactl.py sync-pg-conf""")
    except Exception, ex:
        uLogging.warn("Failed to synchronise DB nodes configuration files with error '%s'" % ex.message)


def getHaMasterAddr(pghaSettings):
    run = lambda cmd: uUtil.runLocalCmd(cmd)
    cmdStatusSql = """PGPASSWORD=%s PGCONNECT_TIMEOUT=10 psql postgres -t -A --username=%s --host=%s --port=%d -c "select pg_is_in_recovery() " """

    # detect status of PG on DB node A
    try:
        aNodeRecoveryState = run(cmdStatusSql % (pghaSettings.monitorAccountPasswd, pghaSettings.monitorAccount, pghaSettings.aDbNode, pghaSettings.haBackendPort)).strip()
    except Exception, ex:
        uLogging.err("Failed to request DB node A with error '%s'" % ex.message)
        raise Exception("PostgreSQL on DB node A did not response. Both DB nodes should be operable")
    uLogging.info("DB node A recovery status '%s'" % aNodeRecoveryState)
    isAMaster = True if aNodeRecoveryState == "f" else False

    # detect status of PG on DB node B
    try:
        bNodeRecoveryState = run(cmdStatusSql % (pghaSettings.monitorAccountPasswd, pghaSettings.monitorAccount, pghaSettings.bDbNode, pghaSettings.haBackendPort)).strip()
    except Exception, ex:
        uLogging.err("Failed to request DB node B with error '%s'" % ex.message)
        raise Exception("PostgreSQL on DB node B did not response. Both DB nodes should be operable")
    uLogging.info("DB node B recovery status '%s'" % bNodeRecoveryState)
    isBMAster = True if bNodeRecoveryState == "f" else False

    # check statuses
    if isAMaster and isBMAster:
        raise Exception("Split Brain of PGHA cluster detected")

    if not isAMaster and not isBMAster:
        raise Exception("Incorrect PGHA cluster state: both DB nodes are slaves")

    return pghaSettings.aDbNode if isAMaster else pghaSettings.bDbNode # one node is Master, another is Slave, so choose Master

def iptablesConfigAllowDb(run, slaveCommunicationIP, masterPort):
    iptablesCmds = []
    iptablesCmds.append(""" iptables -D Postgres -p tcp -s %s --dport %s -j ACCEPT 2> /dev/null || echo -n """ % (slaveCommunicationIP, str(masterPort)))
    iptablesCmds.append(""" iptables -I Postgres 1 -p tcp -s %s --dport %s -j ACCEPT """ % (slaveCommunicationIP, str(masterPort)))
    iptablesCmds.append(""" service iptables save """)

    for ruleCmd in iptablesCmds:
        run(ruleCmd)

def iptablesConfigDenyDb(run, slaveCommunicationIP, masterPort):
    iptablesCmds = []
    iptablesCmds.append(""" iptables -D Postgres -p tcp -s %s --dport %s -j ACCEPT 2> /dev/null || echo -n """ % (slaveCommunicationIP, str(masterPort)))
    iptablesCmds.append(""" service iptables save """)

    for ruleCmd in iptablesCmds:
        run(ruleCmd)

class DeployPgSlaveResult(object):
    pass

def _getPgDbInfo():
    con = uSysDB.connect()
    try:
        cur = con.cursor()
        cur.execute("SELECT inet_server_addr(), inet_server_port(), current_database()")
        return cur.fetchone()
    finally:
        uSysDB.close(con)

def getSqlCommandRunner(targetHostAddr, hostRootPwd=None):
    commandRunner = getCommandRunner(targetHostAddr, hostRootPwd)
    if commandRunner.isLocal:
        return lambda sql: commandRunner("su - postgres -c 'psql -U postgres -c \"%s\"'" % sql)
    else:
        return lambda sql: commandRunner('psql -U postgres -h %s -c "%s"' % (commandRunner.targetHost, sql))

def getCommandRunner(targetHostAddr, hostRootPwd=None):
    targetHostIp = socket.gethostbyname(targetHostAddr)
    return _getCommandRunner(targetHostIp, hostRootPwd)

def _getCommandRunner(targetHostAddr, hostRootPwd):
    if not (targetHostAddr in (x[1] for x in uLinux.listNetifaces())):
        cmdRunner = uUtil.getSSHRemoteRunner(targetHostAddr, hostRootPwd)
        cmdRunner.isLocal = False
    else:
        cmdRunner = lambda cmd: uUtil.runLocalCmd(cmd)
        cmdRunner.isLocal = True
    cmdRunner.targetHost = targetHostAddr
    return cmdRunner

def _tunePgHba(cmdRunner, conMethod, dbName, userName, ip, confPath):
    # tune pg_hba.conf by adding entries like:
    #
    # conMethod    dbName    userName    ip/32    md5
    #
    # e.g.
    # hostssl    replication    oss    1.2.3.4/32    md5
    # host    all    all    1.2.3.4/32    md5
    # etc.
    #
    ipEscaped = ip.replace(".", "\\.")
    # first, remove the line if present
    cmdRunner("sed -i '/^[ \\t]*%s[ \\t]\\+%s[ \\t]\\+%s[ \\t]\\+%s\\/32[ \\t]\\+md5[ \\t]*$/d' %s" % (conMethod, dbName, userName, ipEscaped, confPath))
    # then append
    cmdRunner("sed -i -e '$,+0a\\%s     %s    %s     %s\\/32     md5' %s" % (conMethod, dbName, userName, ipEscaped, confPath))

def deployPgSlave(slaveHostID, isBillingMaster, masterRootPwd, readOnlyUserType, additionalIPs, slaveScript, slaveScriptArgs):
    if not uLogging.logfile:
        uLogging.init2("/var/log/pa/register_slave.log", True, False)
    uLogging.info("Deploying PostgreSQL slave server on PA service node #%d...", slaveHostID)

    masterHostID = 0
    pghaSettings = getPghaSettings()

    if not isBillingMaster:
        if slaveHostID == 1:
            raise Exception("The target slave host is MN: no possibility to use MN node as a database replica.")

        row = _getPgDbInfo()
        databaseName = row[2]
        if pghaSettings.isHa:
            masterAddr = getHaMasterAddr(pghaSettings)
            masterPort = pghaSettings.haBackendPort
            targetReplicationSourceMasterAddr = pghaSettings.vip_2
        else:
            masterAddr = row[0]
            masterPort = int(row[1])
            targetReplicationSourceMasterAddr = masterAddr
        uLogging.info("Master DB location: '%s at %d'" % (masterAddr, masterPort))

        runOnMaster = _getCommandRunner(masterAddr, masterRootPwd)
        if not runOnMaster.isLocal:
            uLogging.info("Master is automation database server running remotely at %s:%d.", masterAddr, masterPort)
        else:
            uLogging.info("Master is automation database server running locally at %s:%d.", masterAddr, masterPort)
            masterHostID = 1
    else:
        if slaveHostID in (b.get_host_id() for b in uBilling.get_billing_hosts()):
            raise Exception("The target slave host is billing node: no possibility to use billing node as a database slave.")
        dbParams = uBilling.PBAConf.getBillingDBPrams()
        masterAddr = uBilling.PBAConf.getBillingDBHost()
        masterPort = int(uBilling.PBAConf.getBillingDBPort())
        databaseName = uBilling.PBAConf.getBillingDBName()
        runOnMaster = _getCommandRunner(masterAddr, masterRootPwd)
        targetReplicationSourceMasterAddr = masterAddr
        uLogging.info("Master is billing database server running at %s:%d.", masterAddr, masterPort)
        masterHostID = None

    isPermitted = False
    slave = uPEM.getHost(slaveHostID)
    if not runOnMaster.isLocal:
        try:
            runCheck = lambda cmd: uUtil.runLocalCmd(cmd)
            checkHostPermittedToBeReplicaOfDB(runCheck, slave.name)
            isPermitted = True
        except:
            pass
    if not isPermitted:
        checkHostPermittedToBeReplicaOfDB(runOnMaster, slave.name)

    slaveCommunicationIP = uPEM.getHostCommunicationIP(slaveHostID)
    ipAddrJoined = ipAddrToUserUniqPostfix(slaveCommunicationIP)
    replUserName = "slave_oa"+ipAddrJoined
    replUserPwd = uUtil.generate_random_password(16)

    runOnSlave = lambda cmd: uHCL.runHCLCmd(slaveHostID, cmd)
    uLogging.info("Slave database server is going to be deployed at %s (%s)", slaveCommunicationIP, slave.name)
    pgsqlOnMaster = uPgSQL.PostgreSQLConfig(commander = runOnMaster)
    pgsqlVer = str(pgsqlOnMaster.get_version_as_int())

    uLogging.info("Current running PostgreSQL version is '%s'" % pgsqlVer)
    verifyPostgresCertificate(pgsqlOnMaster)

    uLogging.info("Instaling PostgreSQL Server on the slave...")
    runOnSlave("yum install -y odin-perftools postgresql%s postgresql%s-server postgresql%s-contrib" % (pgsqlVer, pgsqlVer, pgsqlVer))
    runOnSlave("yum reinstall -y odin-perftools postgresql%s postgresql%s-server postgresql%s-contrib" % (pgsqlVer, pgsqlVer, pgsqlVer))
    uLogging.info("Installation has finished!")

    uLogging.info("Initializing database on slave...")
    pgsqlOnSlave = uPgSQL.PostgreSQLConfig(commander = runOnSlave)
    pgsqlOnSlave.cleanup()
    pgsqlOnSlave.init_db()
    uLinux.configureDatabaseImpl(pgsqlOnSlave, None, [])
    uLogging.info("Saving some slave personal configuration files...")

    slavePersonalFilesBu = []
    slavePersonalFiles = (
        pgsqlOnSlave.get_data_dir()+"/server.key",
        pgsqlOnSlave.get_data_dir()+"/server.crt",
#        pgsqlOnSlave.get_postgresql_conf(),
        pgsqlOnSlave.get_pghba_conf()
    )
    slavePersonalDir = os.path.dirname(pgsqlOnSlave.get_data_dir().rstrip("/"))
    for pf in slavePersonalFiles:
        runOnSlave(""" su - postgres -c 'cp -f "%s" "%s/"' """ % (pf, slavePersonalDir))
        slavePersonalFilesBu.append(os.path.join(slavePersonalDir, os.path.basename(pf)))
    pgsqlOnSlave.stop()
    uLogging.info("Database has been initialized!")

    uLogging.info("Enabling replication connection from slave to master...")
    runOnMaster(""" su - postgres -c "psql --port=%d -c \\"DROP ROLE IF EXISTS %s\\"" """ % (masterPort, replUserName,))
    runOnMaster(""" su - postgres -c "psql --port=%d -c \\"CREATE ROLE %s WITH REPLICATION ENCRYPTED PASSWORD '%s' LOGIN CONNECTION LIMIT 8\\"" """ % (masterPort, replUserName, replUserPwd))

    uLogging.info("Creating read-only user and users to be replicated from master to slave for farther readonly use on the slave node.")
    roUserName = "oa"+ipAddrJoined
    roUserPwd = uUtil.generate_random_password(32)
    # Provide the reentrancy, make sure the database doesn't contain objects created by possible previous launches
    runOnMaster(""" su - postgres -c "psql --port=%d --dbname=%s -c \\"REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM %s\\"" 2> /dev/null || echo -n """ % (masterPort, databaseName, roUserName))
    runOnMaster(""" su - postgres -c "psql --port=%d -c \\"REVOKE EXECUTE ON FUNCTION func_stat_wal_receiver() from %s\\"" 2> /dev/null || echo -n """ % (masterPort, roUserName,))
    runOnMaster(""" su - postgres -c "psql --port=%d -c \\"DROP ROLE IF EXISTS %s\\"" """ % (masterPort, roUserName,))
    runOnMaster(""" su - postgres -c "psql --port=%d -c \\"CREATE ROLE %s WITH ENCRYPTED PASSWORD '%s' LOGIN\\"" """ % (masterPort, roUserName, roUserPwd))

    #add ability to monitor replication status for RO user
    def psql_as_postgres(input):
        return r'su - postgres -c "psql --port=%d -c \"%s\""' % (masterPort, input)
    runOnMaster(psql_as_postgres("DROP FUNCTION IF EXISTS func_stat_wal_receiver();"))
    psql11_fields = []
    if LooseVersion(pgsqlVer) >= LooseVersion("11"):
        psql11_fields = ["cast('' as text) as sender_host", "-1 as sender_port"]
    pg_stat_wal_receiver_sql = 'CREATE FUNCTION func_stat_wal_receiver() RETURNS SETOF pg_stat_wal_receiver as '
    columns_to_select = ", ".join(["pid", "status", "receive_start_lsn", "receive_start_tli", "received_lsn", "received_tli",
                                   "last_msg_send_time", "last_msg_receipt_time", "latest_end_lsn", "latest_end_time",
                                   "cast('' as text) as slot_name"] +
                                   psql11_fields +
                                   ["cast('' as text) as conninfo"])
    pg_stat_wal_receiver_sql += r'\\$\\$ select %s from pg_stat_wal_receiver; \\$\\$ LANGUAGE sql SECURITY DEFINER;' % columns_to_select
    runOnMaster(psql_as_postgres(pg_stat_wal_receiver_sql))
    runOnMaster(psql_as_postgres("REVOKE EXECUTE ON FUNCTION func_stat_wal_receiver() FROM public;"))
    runOnMaster(psql_as_postgres("GRANT EXECUTE ON FUNCTION func_stat_wal_receiver() to %s;" % roUserName))

    if readOnlyUserType == "uinode":
        uiBoosterTables = ("aps_resource", "aps_property_value", "aps_resource_link", "aps_application", "aps_property_info",
                           "aps_package", "aps_relation_info", "aps_relation_types", "aps_type_info", "aps_type_inheritance", "aps_package_series", "aps_package_service",
                           "aps_property_enum_info", "aps_type_info_to_package",
                           "aps_operation_param", "aps_operation_info")
        runOnMaster(""" su - postgres -c "psql --port=%d --dbname=%s -c \\"GRANT SELECT ON TABLE %s TO %s\\"" """ % (masterPort, databaseName, ",".join(uiBoosterTables), roUserName))
    else:
        runOnMaster(""" su - postgres -c "psql --port=%d --dbname=%s -c \\"GRANT SELECT ON ALL TABLES IN SCHEMA public TO %s\\"" """ % (masterPort, databaseName, roUserName))
    uLogging.info("Read-only user has been created.")

    _tunePgHba(runOnMaster, "hostssl", "replication", replUserName, slaveCommunicationIP, pgsqlOnMaster.get_pghba_conf())

    if int(getWalKeepSegments(runOnMaster, masterPort)) != 16384:
        runOnMaster(""" sed -i '/^[ \t]*wal_keep_segments[ \t]*=.*/d' "%s" """ % (pgsqlOnMaster.get_postgresql_conf(),))
        runOnMaster(""" sed -i -e '$,+0a\wal_keep_segments = 16384' "%s" """ % (pgsqlOnMaster.get_postgresql_conf(),))

    #For more details see the following KB: https://kb.cloudblue.com/en/115916
    #Chain called Postgres could be absent if KB is not applied, so that we have to add that rules only in case if KB applied
    if runOnMaster(""" iptables -nL Postgres 2> /dev/null || echo -n """):
        uLogging.info("Configuring iptables for replication access")
        iptablesConfigAllowDb(run = runOnMaster, slaveCommunicationIP= slaveCommunicationIP, masterPort=masterPort)
        uLogging.info("Configuring iptables on master done!")

        if pghaSettings.isHa:
            pghaSlaveAddr = pghaSettings.bDbNode if masterAddr == pghaSettings.aDbNode else pghaSettings.aDbNode
            uLogging.info("Configuring iptables for replication access on PGHA slave '%s'" % pghaSlaveAddr)
            runOnPghaSlave = uUtil.getSSHRemoteRunner(pghaSlaveAddr, masterRootPwd) # providing of password is an extra measure since SSH certificates are distributed
            iptablesConfigAllowDb(run = runOnPghaSlave, slaveCommunicationIP= slaveCommunicationIP, masterPort=masterPort)
            uLogging.info("Configuring iptables o PGHA slave done!")

    pgsqlOnMaster.reload()
    uLogging.info("Replication connection has been enabled!")

    if pghaSettings.isHa:
        forceHaMasterSyncConf(runOnMaster)

    uLogging.info("Setting up initial database replication...")
    cleanPgCertificate(pgsqlOnSlave.get_data_dir(), runOnSlave) # clean certificate if exists
    baseBackupCmd = """ su - postgres -c 'PGPASSWORD=%s "%s/pg_basebackup" -X stream --host=%s --port=%s
"--pgdata=%s" "--username=%s" --write-recovery-conf --checkpoint=fast' """ % (replUserPwd, pgsqlOnSlave.get_bin_dir(), targetReplicationSourceMasterAddr, str(masterPort), pgsqlOnSlave.get_data_dir(), replUserName)
    pgsqlOnSlave.cleanup()
    #targeting errors like f.e. this-> ERROR:  could not open file "./pg_hba.conf.bak": Permission denied
    runOnMaster(""" chown -R postgres:postgres "%s" """ % (pgsqlOnMaster.get_data_dir(),))
    runOnSlave(baseBackupCmd)
    uLogging.info("Initial database replication has been done!")

    uLogging.info("Doing post-configuration...")

    dotPostgresDir = os.path.dirname(os.path.dirname(pgsqlOnSlave.get_data_dir().rstrip("/"))) + "/.postgresql"
    runOnSlave(""" su - postgres -c 'mkdir -p "%s"' """ % (dotPostgresDir,))
    runOnSlave(""" su - postgres -c 'cp -f "%s/%s" "%s/%s"' """ % (pgsqlOnSlave.get_data_dir(), "server.crt", dotPostgresDir, "root.crt"))

    for i, pf in enumerate(slavePersonalFilesBu):
        runOnSlave(""" su - postgres -c 'mv -f "%s" "%s/"' """ % (pf, os.path.dirname(slavePersonalFiles[i])))

    uLinux.tunePostgresParamsImpl(pgsqlOnSlave)

    runOnSlave("sed -i -E 's|(.*[ \\t]+sslmode[ \\t]*=[ \\t]*)prefer([ \\t]+.*)|\\1verify-ca\\2|g' \"%s/recovery.conf\" " % (pgsqlOnSlave.get_data_dir().rstrip("/"),))
    #marking server as a hot standby
    runOnSlave(""" sed -i '/^[ \t]*hot_standby[ \t]*=.*/d' "%s" """ % (pgsqlOnSlave.get_postgresql_conf(),))
    runOnSlave(""" sed -i -e '$,+0a\\hot_standby = on' "%s" """ % (pgsqlOnSlave.get_postgresql_conf(),))
    if additionalIPs is not None:
        for ip in additionalIPs:
            ipEsc = ip.replace(".", "\\.")
            runOnSlave(""" sed -i -e '$,+0a\hostssl     all    all     %s\/32     md5' "%s" """ % (ipEsc, pgsqlOnSlave.get_pghba_conf()))
    runOnSlave(""" sed -i '/^listen_addresses/s/\*/127.0.0.1/g' "%s" """ % (pgsqlOnSlave.get_postgresql_conf(),))
    uLogging.info("Post-configuration has been done!")

    uLogging.info("Starting new slave database server!")
    pgsqlOnSlave.restart()
    pgsqlOnSlave.set_autostart()
    waitSlaveRecoveryComplete(runOnSlave) # make sure recovery stage is complete

    uLinux.tunePostgresLogs(runOnSlave)
    pgsqlOnSlave.reload()
    uLogging.info("New slave database server has started!")

    if slaveScript:
        uLogging.info("Running post configuration script on slave: %s", slaveScript)
        cbCmd = """python "%s" connect_slave "%s" "%s" "%s" "%s" """ % (slaveScript, slaveCommunicationIP, databaseName, roUserName, roUserPwd)
        for a in slaveScriptArgs:
            cbCmd = cbCmd + ' "%s" ' % a
        runOnSlave(cbCmd)
        uLogging.info("Post configuration has been done!")

    rv = DeployPgSlaveResult()
    rv.replUserName = replUserName
    rv.roUserName = roUserName
    rv.masterHostID = masterHostID
    rv.masterAddr = masterAddr
    return rv

def cleanPgCertificate(pgDataPath, run):
    dotPostgresDir = os.path.dirname(os.path.dirname(pgDataPath.rstrip("/"))) + "/.postgresql"
    crtFilePath = os.path.join(dotPostgresDir, "root.crt")
    run("""rm -f "%s" 2> /dev/null""" % crtFilePath)

def waitSlaveRecoveryComplete(run):
    recoveryComplete = False
    waitRecoveryEnd = 0
    while waitRecoveryEnd < PG_SLAVE_END_RECOVERY_TIMEOUT_SECONDS:
        try:
            run("""su - postgres -c "psql -t -P format=unaligned -c $'show server_version'" """ )
            recoveryComplete = True
            break
        except Exception, e:
            errorMessage = e.message
            if errorMessage.find("system is starting") != -1:
                uLogging.warn("Slave database is in recovery mode:\n%s\n'%s'\n%s " % ("="*40 , errorMessage , "="*40))
            else:
                raise Exception("Failed to start slave database server with error '%s'!" % errorMessage)

        time.sleep(5)
        waitRecoveryEnd += 5
        uLogging.info("Wait until PG is out of the recovery stage. Elapsed '%d' seconds" % waitRecoveryEnd)

    if not recoveryComplete:
        raise Exception("Slave PostgreSQL did not complete recovery stage in '%d' seconds" % PG_SLAVE_END_RECOVERY_TIMEOUT_SECONDS)

def removePgSlave(slaveHostID, masterRootPwd):
    if not uLogging.logfile:
        uLogging.init2("/var/log/pa/deregister_slave.log", True, False)

    slave = uPEM.getHost(slaveHostID)
    slaveCommunicationIP = uPEM.getHostCommunicationIP(slaveHostID)
    runOnSlave = lambda cmd: uHCL.runHCLCmd(slaveHostID, cmd)
    uLogging.info("Slave database server at %s (%s) is going to be removed.", slaveCommunicationIP, slave.name)

    pghaSettings = getPghaSettings()

    pgsqlOnSlave = None
    try:
        pgsqlOnSlave = uPgSQL.PostgreSQLConfig(commander = runOnSlave)
    except Exception, e:
        uLogging.info("Could not find slave database server at %s (%s): %s", slaveCommunicationIP, slave.name, str(e))
        return

    conInfoDict = {}
    recoveryConf = getRecoveryConf(runOnSlave, pgsqlOnSlave.get_data_dir())
    conInfoRe = re.compile("^[ \t]*primary_conninfo[ \t]*=[ \t]*'(.*)'$")
    for l in recoveryConf.split('\n'):
        conMatch = conInfoRe.match(l)
        if conMatch:
            for kv in conMatch.group(1).split(" "):
                kv = kv.strip()
                if kv:
                    k, v = kv.split("=", 1)
                    conInfoDict[k.strip()] = v.strip()
            break

    runOnMaster = None

    recoveryHost = conInfoDict["host"]

    if pghaSettings.isHa:
        masterAddr = getHaMasterAddr(pghaSettings)
        masterPort = pghaSettings.haBackendPort
    else:
        masterAddr = recoveryHost
        masterPort = int(conInfoDict["port"])

    if recoveryHost != uPEM.getHostCommunicationIP(1): #MN node?
        billingHostID = None
        runOnMaster = None
    else:
        uLogging.info("Master is automation database server running locally at %s:%d.", masterAddr, masterPort)
        runOnMaster = lambda cmd: uUtil.runLocalCmd(cmd)
    if runOnMaster is None: #Master is running as an external database server
        uLogging.info("Master is automation database server running remotely at %s:%d.", masterAddr, masterPort)
        runOnMaster = uUtil.getSSHRemoteRunner(masterAddr, masterRootPwd)

    pgsqlOnMaster = uPgSQL.PostgreSQLConfig(commander = runOnMaster)
    replUserName = conInfoDict["user"]
    uLogging.info("Disabling replication connection from slave to master...")
    ipEscpd = slaveCommunicationIP.replace(".", "\\.")
    runOnMaster(""" sed -i '/^[ \t]*hostssl[ \t]\+replication[ \t]\\+%s[ \t]\+%s\/32[ \t]\+md5[ \t]*/d' "%s" """ % (replUserName, ipEscpd, pgsqlOnMaster.get_pghba_conf()))
    runOnMaster(""" su - postgres -c "psql --port=%d -c \\"DROP ROLE IF EXISTS %s\\"" """ % (masterPort, replUserName,))

    if pghaSettings.isHa:
        forceHaMasterSyncConf(runOnMaster)

    uLogging.info("Dropping slave read only user...")
    runOnMaster(r'su - postgres -c "psql --port=%d -c \"DROP FUNCTION IF EXISTS func_stat_wal_receiver();\""' % masterPort)
    roUserName = "oa"+ipAddrToUserUniqPostfix(slaveCommunicationIP)
    for db in listPgDatabases(runOnMaster, masterPort):
        db = db.strip()
        if not (db in ("postgres", "template0", "template1")):
            runOnMaster(""" su - postgres -c "psql --port=%d --dbname=%s -c \\"REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM %s\\"" 2> /dev/null || echo -n """ % (masterPort, db, roUserName))
    runOnMaster(""" su - postgres -c "psql --port=%d -c \\"DROP ROLE IF EXISTS %s\\"" """ % (masterPort, roUserName,))

    if runOnMaster(""" iptables -nL Postgres 2> /dev/null || echo -n """):
        uLogging.info("Dropping iptables rules...")
        iptablesConfigDenyDb(run = runOnMaster, slaveCommunicationIP = slaveCommunicationIP, masterPort=masterPort)
        uLogging.info("Iptables rules on master are dropped!")

        if pghaSettings.isHa:
            pghaSlaveAddr = pghaSettings.bDbNode if masterAddr == pghaSettings.aDbNode else pghaSettings.aDbNode
            runOnPghaSlave = uUtil.getSSHRemoteRunner(pghaSlaveAddr, masterRootPwd) # providing of password is an extra measure since SSH certificates are distributed
            uLogging.info("Dropping PGHA slave iptables rules...")
            iptablesConfigDenyDb(run = runOnPghaSlave, slaveCommunicationIP = slaveCommunicationIP, masterPort=masterPort)
            uLogging.info("Iptables rules on PGHA slave are dropped!")

    uLogging.info("Stopping slave server...")
    pgsqlOnSlave.stop()
    uLogging.info("Reloading master configuration...")
    pgsqlOnMaster.reload()
    uLogging.info("Cleanup slave server data...")
    pgsqlOnSlave.cleanup()
    cleanPgCertificate(pgsqlOnSlave.get_data_dir(), runOnSlave) # delete certificate
    uLogging.info("Removing slave has finished!")

def allowTcpConnectionsFromHost(hostIp, pgDbServerRootPwd):
    pgDbServerIp = _getPgDbInfo()[0]
    pgDbServerCmd = _getCommandRunner(pgDbServerIp, pgDbServerRootPwd)
    pgDb = uPgSQL.PostgreSQLConfig(commander=pgDbServerCmd)
    _tunePgHba(pgDbServerCmd, "host", "all", "all", hostIp, pgDb.get_pghba_conf())
    pgDb.reload()

__all__ = ["deployPgSlave", "removePgSlave"]
