# -*- coding: utf-8 -*-

import time
import os
import copy
import uTextRender
import uLogging
import uSysDB
import uUtil
import codecs
import socket
import re 
from uConst import Const

class PrecheckFailed(Exception):

    """
    Exception to throw from precheck action to indicate, that it failed
    """

    def __init__(self, reason, what_to_do = None):
        message = "Precheck error: %s" % reason
        if not message.endswith('\n'):
            message += '\n'
        if what_to_do:
            message += "Do the following: %s\n" % what_to_do
        Exception.__init__(self, message)
        self.reason = reason
        self.what_to_do = what_to_do


def print_precheck_message_to_report(report_file, action_id, action_owner, message, counter):
    try:
        lines = message.splitlines()
        if len(lines) > 1:
            report_file.write(" 1.%-3s %s [%s]%s\n" % (str(counter) + '.', action_id, action_owner, ':'))
            for line in lines:
                report_file.write("\t" + line.strip() + "\n")
        else:
            report_file.write(" 1.%-3s %s [%s]: %s\n" % (str(counter) + '.', action_id, action_owner, lines[0]))
        report_file.write('\n')
    except:
        uUtil.logLastException()
        report_file.write('\n')


def process_precheck_report(build_info, version, poa_version, config):

    errors = []
    messages = []
    now = time.localtime()
    report_filename = time.strftime("precheck-report-%Y-%m-%d-%H%M%S.txt", now)
    report_filename = os.path.abspath(os.path.join(os.path.dirname(config.log_file), report_filename))
    report_file = codecs.open(report_filename, encoding='utf-8', mode='w+')

    for action_id, action_owner, result in precheck_results:
        if not result:
            message = "OK\n"
            messages.append((action_id, action_owner, result, message))
        elif isinstance(result, Exception):
            message = ""
            if isinstance(result, PrecheckFailed):
                if not result.reason.endswith('\n'):
                    result.reason += '\n'
                message += "%s" % result.reason
                if result.what_to_do:
                    message += "You should: %s\n" % result.what_to_do
                else:
                    message += "\n"
            else:
                message += " UNEXPECTED ERROR. See precheck log for details. Failed to complete precheck action %s [%s]: %s\n" % (
                    action_id, action_owner, result)

            errors.append((action_id, action_owner, result, message))
        else:
            message = "%s\n" % result
            messages.append((action_id, action_owner, result, message))

    con = uSysDB.connect()
    cur = con.cursor()
    cur.execute("SELECT company_name FROM accounts WHERE account_id = 1")
    company_name, = cur.fetchone()
    # TODO rewrite on PEMVersion.getCurrentVersion
    cur.execute("SELECT build FROM version_history ORDER BY install_date DESC")
    build_id, = cur.fetchone()
    cur.execute("SELECT name FROM hotfixes ORDER BY install_date DESC")
    hotfixes = cur.fetchone()

    report_file.write("Operation Automation Upgrade Precheck Report for '%s'\n\n" % company_name)
    report_file.write("Current domain:            %s\n" % socket.getfqdn())
    report_file.write("Date of report:            %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S", now)))
    if not hotfixes:
        hotfix = ""
    else:
        hotfix = " (%s)" % hotfixes[0]
    report_file.write("Current Operation Automation build:         %s%s\n" % (build_id, hotfix))
    target_build_id = ""
    for ver in build_info.version_list:
        name, build_ver, built, kind = ver
        target_build_id += "%s " % build_ver
    report_file.write("Target Operation Automation build:          %s\n" % target_build_id)

    report_file.write("Precheck version:          %s\n" % version)
    report_file.write("Operation Automation version:               %s\n" % poa_version)

    if errors:
        report_file.write(
            "\n%2s. Following errors need to be fixed before upgrade can be continued (refer also to '3. Additional information')\n\n" % '1')
        counter = 1
        for action_id, action_owner, result, message in errors:
            print_precheck_message_to_report(report_file, action_id, action_owner, message, counter)
            counter += 1
        report_file.write("\n%2s. Following checks have passed without errors\n" % '2')
    else:
        report_file.write(
            "%2s. Success\n%6sNo issues preventing upgrade were found: you may continue with upgrade, though before that, please, check results below.\n\n" % ('1', ' '))

    skipped_table = uTextRender.Table(indent=2)
    skipped_table.setHeader(["Owner", "Skipped actions"])

    results_skipped = {}
    results_fine = ''
    results_fine_order = {}
    succeeded, skipped, other = 0, 0, 0
    other_results = ''
    for action_id, action_owner, result, message in messages:
        try:
            if result and ', skipping' in result:
                skipped += 1
                if not results_skipped.has_key(result):
                    results_skipped[result] = ''
                results_skipped[result] += "%s\n" % action_id
            elif result and ', skipping' not in result:
                other += 1
                other_results += ' %s.%-3s %s [%s]:\n       %s\n' % (
                    '3', str(other) + '.', action_id, action_owner, result.replace('\n', '\n       '))
            else:
                succeeded += 1
                if not results_fine_order.has_key(result):
                    results_fine_order[result] = 0
                if results_fine_order[result] < 1:
                    results_fine += "  %-85s" % ("%s [%s]" % (action_id, action_owner))
                    results_fine_order[result] += 1
                else:
                    results_fine += "  %s\n" % ("%s [%s]" % (action_id, action_owner))
                    results_fine_order[result] = 0
        except Exception, e:
            other_results += ' %s.%-3s *** Processing of action %s FAILED: %s. Check %s\n' % (
                '3', str(other) + '.', action_id, e, config.log_file)
            uUtil.logLastException()
        except:
            other_results += ' %s.%-3s *** Processing of action %s FAILED: %s. Check %s\n' % (
                '3', str(other) + '.', action_id, 'unknown error', config.log_file)
            uUtil.logLastException()

    failed = len(errors)
    succeeded += other
    total = len(messages) + failed

    report_file.write("\n%4s. Following checks have succeeded\n\n" % '2.1')
    report_file.write(results_fine)
    if not results_fine.endswith('\n'):
        report_file.write('\n')
    report_file.write("\n%4s. Following checks have been skipped\n" % '2.2')

    # process skipped actions:
    for key in results_skipped:
        skipped_table.addRow([key.replace(', skipping', ''), results_skipped[key]])

    report_file.write("\n%s\n" % skipped_table)

    report_file.write("\n%2s. Additional information:\n" % '3')
    report_file.write(other_results)

    report_file.close()

    if errors:
        uLogging.info("Some of pre-upgrade checks failed. Pre-upgrade checks report summary:")
        uLogging.info("    Failed: %-3s Succeeded: %-3s Skipped: %-3s Total: %-3s" % (failed, succeeded, skipped, total))
        uLogging.info("    FAILURE. The report was saved to %s" % report_filename)
        uLogging.info("    See detailed precheck log in %s " % config.log_file)
        return False
    else:
        uLogging.info("Success. No checks failed. Pre-upgrade checks report summary:")
        uLogging.info("    Failed: %-3s Succeeded: %-3s Skipped: %-3s Total: %-3s" % (failed, succeeded, skipped, total))
        uLogging.info("    Success. No checks failed. The report was saved to %s" % report_filename)
        uLogging.info("    See detailed precheck log in %s " % config.log_file)
        return True


def _precheck_for_deprecated_os(node_id):
    import uLinux
    try:
        if node_id == 1:
            uLinux.check_platform_supported(uLinux.determinePlatform())
        else:
            uLinux.check_platform_supported(uLinux.determineNodePlatform(node_id))
        return None
    except Exception, e:
        uLogging.save_traceback()
        return e.args[0]


def warn_precheck_for_deprecated_os():
    import uBilling
    nodes = set([1])
    nodes.update(uBilling.get_billing_platform_hosts().values())
    results = [(node_id, _precheck_for_deprecated_os(node_id)) for node_id in nodes]
    errors = filter(lambda result: result[1], results)
    if errors:
        fail_reason = '\n'.join(map(str, errors))
        failed_nodes = [error[0] for error in errors]
        raise PrecheckFailed(fail_reason, 'Upgrade Linux on nodes %s to minimal supported version: %s'
                                        % (failed_nodes, Const.getMinSupportedLinux()))

def precheck_for_helm_version():
    import uHelm
    helm = uHelm.Helm()
    if not helm.isHelmInstalled(): return
    if helm.isHelmUpgradeRequired():
        fail_reason = 'Helm upgrade to version %s is required' % helm.getTargetHelmVersion()
        fail_resolution = 'Upgrade Helm on the Managment Node to version %s using commands:\n%s' % (
            helm.getTargetHelmVersion(), '\n'.join(helm.getHelmUpgradeCommands()))
        raise PrecheckFailed(fail_reason, fail_resolution)

def precheck_for_access_verify_db(config):
    uLogging.info("Checking verify_db exists...")
    import uDBValidator
    import uConfig
    config_v = copy.copy(config)
    config_v.database_name = config_v.database_name + '_verify'
    try:
        uSysDB.init(config_v)
        con_v = uSysDB.connect()
    except Exception, e:
        uLogging.debug(str(e))
        uLogging.warn("%s DB does not exist" % config_v.database_name)
        try:
            if config_v.admin_db_password or uUtil.isLocalAddress(config_v.database_host):
                # try to create verify db:
                uLogging.info("Trying to create '%s' database..." % config_v.database_name)
                uDBValidator._recreate_verify_db(config_v)
                uLogging.info("'%s' is created successfully." % config_v.database_name)
            else:
                raise Exception("Postgres admin user credentials are required to create %s" % config_v.database_name)
        except Exception, e:
             uLogging.debug(str(e))
             dsn_login_short = re.sub("@.*", "", config_v.dsn_login)
             raise PrecheckFailed(
                reason="'%s' database is not accessible or does not exist" % config_v.database_name,
                what_to_do="Connect to %s Postgres server as admin user and create database: 'CREATE DATABASE %s OWNER %s'. If database '%s' already exists, make sure its owner is '%s'." % (config_v.database_host, config_v.database_name, dsn_login_short, config_v.database_name, dsn_login_short)
             )
    finally:
        uSysDB.init(config)
        uSysDB.disconnect_all()

def check_bm_sdk():
    from poaupdater import uPackaging
    pkg_name = 'bm-sdk'
    hosts = [t.host_id for t in uPackaging.listInstalledPackages(pkg_name, 'other')]
    if len(hosts) > 0:
        raise PrecheckFailed(
            reason='"%s" is installed on host(s): %s' % (pkg_name, hosts),
            what_to_do='Remove package "%s" from host(s): %s' % (pkg_name, hosts)
        )


def check_java_package_availability():
    import uLinux
    package_name = 'java-11-openjdk'
    if not uLinux.is_yum_package_provided(package_name):
        raise PrecheckFailed(
            reason='Package "%s" is not provided by any YUM repository' % package_name,
            what_to_do='Enable OS repositories in the YUM configuration directory: "/etc/yum.repos.d/"'
        )

def kubernetes_health_precheck(helms_to_update):
    import uHelm
    try:
        uHelm.clusterHealthPrecheck(helms_to_update)
    except uHelm.notEnoughResourcesException, e:
        uUtil.logLastException()
        raise PrecheckFailed(
            reason=e.message,
            what_to_do='Add more resources to Kubernetes cluster'
        )
    except uHelm.pendingPodsException, e:
        uUtil.logLastException()
        return e.message
    except Exception, e:
        uUtil.logLastException()
        raise PrecheckFailed(
            reason=e.message,
            what_to_do='Check Tiller and Kubernetes cluster accessibility'
        )

precheck_results = []
