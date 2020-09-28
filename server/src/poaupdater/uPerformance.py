__author__ = 'imartynov'

import sys
import os
from uConst import Const

from poaupdater import uUtil, uLogging
if not Const.isWindows():
    from poaupdater import uPgSQL


def tuneDatabase(config):
    uLogging.debug("tuneDatabase started, scale_down: %s" % config.scale_down)
    if not Const.isWindows() and config.scale_down:
        uLogging.debug("tuning PgSQL")
        p = uPgSQL.PostgreSQLConfig()

        pg_conf = p.get_postgresql_conf()
        env = os.environ.copy()
        # 2147483648 bytes = 2 GB
        # 2 GB limit is set because 'shared_buffers' should be equal to 512 mb
        uUtil.readCmdExt(["odin-pg-tune", "-f", "--input-config=" + pg_conf, "--min-connections=128", "--output-config=" + pg_conf, "--memory=2147483648"], env = env)

        uLogging.debug("restarting PgSQL...")
        p.restart()
    else:
        uLogging.debug("nothing done")


def tuneJBoss(config):
    uLogging.debug("tuneJBoss started, scale_down: %s" % config.scale_down)
    if not Const.isWindows() and config.scale_down:
        from u import bootstrap
        jbossdir = bootstrap.getJBossDir(config.rootpath)

        uLogging.info("Tuning JBoss connection pool")
        bootstrap.execCLI(
            jbossdir, 'embed-server --server-config=%s,' % bootstrap.serverConfig + '/subsystem=datasources/data-source=pauds:write-attribute(name="max-pool-size", value="80")')
        # jboss restart required, performed after PUI deployment
    else:
        uLogging.debug("nothing done")
