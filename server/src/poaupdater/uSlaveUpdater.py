import ntpath
import os
import posixpath
import ssl
import tarfile
import re
import urllib2
import uThreadPool
import uHCL
import uAction
import uLogging
import uPEM
import uUtil
import uBuild
import uLinux
import uDialog
import threading
from pprint import pformat
import uPackaging
from uConst import Const
from time import sleep
import datetime
from collections import namedtuple


FailedHost = namedtuple("FailedHost", ["host", "error"])

class TaskItem(object):
    def __init__(self, host, paagent_dist_url):
        self.host = host
        self.paagent_dist_url = paagent_dist_url

    def __repr__(self):
        return 'task for host {host}'.format(host=self.host)


def preparePool(config):
    fun = lambda task_item: update_slave(task_item, config)
    pool = uThreadPool.ThreadPool(fun)
    return pool

def report_slave_upgrade_status(binfo, pool, slaves_count):

    def cut_ms(time_delta):
        return str(time_delta).split(".")[0]

    threads_count = pool.threads_count
    upgraded_slaves = len(binfo.progress.updated_hosts)
    failed_slaves = len(binfo.progress.failed_hosts)
    not_yet_upgraded_slaves = slaves_count - failed_slaves - upgraded_slaves
    pool_results = pool.results + pool.outputQ
    processed_slaves = len(set([result.task_item.host.host_id for result in pool_results]))
    not_processed_slaves = slaves_count - processed_slaves
    durations = [task_result.duration for task_result in pool_results]

    if pool_results:
        avg_duration = sum(durations, datetime.timedelta(0)) / len(durations)
        tentative_time_to_finish = avg_duration * int(round((not_processed_slaves / float(threads_count))))

        if not tentative_time_to_finish:
            tentative_time_to_finish = cut_ms(avg_duration) + " (almost done)"

    else:
        avg_duration = tentative_time_to_finish = "[no threads processed]"

    report_message = "Slave upgrade statistics below. \n\n" \
                     "Upgrade pool status: \n" \
                     " - threads count {threads_count} \n" \
                     " - slaves count {slaves_count} \n" \
                     " - processed slaves {processed_slaves} \n" \
                     " - not processed slaves {not_processed_slaves} \n" \
                     " - average job duration {avg_duration} \n" \
                     " - tentative time to finish {tentative_time_to_finish} \n\n" \
                     "Checked upgrade results: \n" \
                     " - upgraded slaves {upgraded_slaves} \n" \
                     " - not yet upgraded/not checked slaves {not_yet_upgraded_slaves} \n" \
                     " - skipped slaves {failed_slaves} \n".format(
        threads_count=threads_count, slaves_count=slaves_count, upgraded_slaves=upgraded_slaves,
        not_yet_upgraded_slaves=not_yet_upgraded_slaves, failed_slaves=failed_slaves, processed_slaves=processed_slaves,
        avg_duration=cut_ms(avg_duration), not_processed_slaves=not_processed_slaves,
        tentative_time_to_finish=cut_ms(tentative_time_to_finish))

    uLogging.debug(report_message)

    return report_message


class ProcessedResult(object):
    def __init__(self, pool_result):
        self.pool_result = pool_result
        self.successful = False
        self.error_as_text = pformat(pool_result.result)
        self.process_result()

    def process_result(self):
        host = self.pool_result.task_item.host
        upgrade_result = self.pool_result.result
        without_exception = not isinstance(upgrade_result, Exception)
        empty_result = upgrade_result is None

        if without_exception and not empty_result and upgrade_result is True:
            self.successful = True
        elif empty_result:
            uLogging.err("Slave {host} upgrade failed. Check details in log.".format(host=host))
        else:
            uLogging.err("Slave {host} upgrade failed. Details: \n{error_as_text}".format(
                host=host, error_as_text=self.error_as_text))


def dialog_need_retry(host):
    try:
        need_retry = uDialog.askYesNo(
            question="Slave {host} upgrade failed, do you want to retry?".format(host=host), timeout = 20)
    except KeyboardInterrupt:
        need_retry = False

    return need_retry


def process_one_result(pool_result, pool, binfo, config):
    processed_result = ProcessedResult(pool_result)
    host = pool_result.task_item.host

    if not processed_result.successful and config.batch:
        pool.terminateLocked()
        raise Exception("Slave upgrade failed, batch mode is active")

    if not processed_result.successful:

        if dialog_need_retry(host):
            pool.put(pool_result.task_item)
            uLogging.warn("Slave {host} scheduled for retry".format(host=host))
        else:
            uLogging.warn("Slave {host} failed to update, retry is skipped".format(host=host))
            binfo.progress.failed_hosts.append(
                FailedHost(host=host, error=processed_result.error_as_text)
            )
    else:
        binfo.progress.updated_hosts.add(host.host_id)



def process_pool_results(pool, binfo, config):
    upgrade_status_changed_event.set()

    while True:
        pool_result = pool.get_result()

        if pool_result is None:
            upgrade_status_changed_event.set()
            break

        process_one_result(pool_result, pool, binfo, config)


def prepare_request_for_repourl_updating(request, config):
    """Filling the request object with corresponding commands for updating yum repourl

    :param request - uHCL.Request() object
    :param config

    :return request
    """
    uLogging.debug("Preparing request for updating pa-central repo")
    yum_repo_url = posixpath.join(config.yum_repo_url, Const.getDistribLinDir(), "$releasever/")
    proxy = "proxy=%s" % config.yum_repo_proxy_url if config.yum_repo_proxy_url else ""
    contents = config.PA_YUM_REPO_CONF_TEMPLATE % {"url": yum_repo_url, "proxy": proxy}
    request.rm("/etc/yum.repos.d/poa.repo")  # remove old poa.repo config file
    request.mkfile(config.PA_YUM_REPO_FILE, contents, owner="root", group="root", perm="0600", overwrite=True)
    request.command("yum clean all --disablerepo=* --enablerepo=pa-central-repo")
    request.command("yum makecache --disablerepo=* --enablerepo=pa-central-repo")
    request.command("yum -q check-update", valid_exit_codes=[0, 100])
    return request


def prepare_request_for_rpm_updating(request, task_item):
    """Filling the request object with corresponding commands for updating yum repourl
    :param request - uHCL.Request() object
    :param task_item
    :return request
    """
    uLogging.debug("Preparing request for updating pa-agent RPM")
    remote_temp_dir = get_remote_temp_dir(task_item.host)
    transferred_agent_rpm = get_remote_agent_rpm_path(task_item.host)

    request.fetch(
        srcfile=posixpath.basename(task_item.paagent_dist_url),
        urls=[posixpath.dirname(task_item.paagent_dist_url)],
        dstvar="archive"
    )
    request.extract("${archive}", remote_temp_dir)
    request.command("yum install -y --nogpgcheck {agent_rpm}".format(agent_rpm=transferred_agent_rpm),
                    valid_exit_codes=[0, 1], stdout='stdout', stderr='stderr', retvar='retcode')
    return request


def update_linux_slave(task_item, config):
    uLogging.debug("Updating Linux slave {host}".format(host=task_item.host))
    # Initializing request object
    request = uHCL.Request(task_item.host.host_id, user='root', group='root')

    # Preparing the instructions if update repourl is necessarily
    if config.need_update_yum_repourl:
        request = prepare_request_for_repourl_updating(request, config)

    # Filling request object with corresponding commands if paagent_dist_url is not a fake
    if task_item.paagent_dist_url:
        request = prepare_request_for_rpm_updating(request, task_item)

    return request.performCompat()


manual_upgrade_inst = """
Please upgrade the agent manually:
\t1. Go to node '%s' (if it is cluster node, you have to execute the following steps on each node of the cluster).
\t2. Copy PAgent.exe from distribution to the c:\\program files\\swsoft\\pem\\tmp\\ folder
\t3. Click 'Start > Run' and enter the following command line:
\t   c:\\program files\\swsoft\\pem\\tmp\\PAgent.exe /qr /l c:\\pemupgrade_manual.log
\t   (Path to installation folder can differ on concrete installations)
\t4. Ensure that the upgrade has been completed successfully (no error messages).
"""

fail_reasons_list = """
POA Agent upgrade may fail by the following reasons. It is recommended that you check and troubleshoot them if necessary.
\t1. Agent has not started during MSI upgrade.
\t2. DCOM is mal-functional.
\t3. Connectivity problems with Management Node.
\t4. Cluster service was down on cluster node
\t5. Agent hasn't stopped during MSI upgrade
\t6. Security problems
\t7. WMI service was down or mal-functional
\t8. Disk space is exhausted on upgraded node
\t9. Other specific issues of concrete customer's installation
Also check c:\\pemupgrade.log on target node for problem details.
"""

msi_errors = {
    13: "The data is invalid.",
    87: "One of the parameters was invalid.",
    120: "This value is returned when a custom action attempts to call a function that cannot be called from custom actions. The function returns the value ERROR_CALL_NOT_IMPLEMENTED. Available beginning with Windows Installer version 3.0.",
    1259: "If Windows Installer determines a product may be incompatible with the current operating system, it displays a dialog box informing the user and asking whether to try to install anyway. This error code is returned if the user chooses not to try the installation.",
    1601: "The Windows Installer service could not be accessed. Contact your support personnel to verify that the Windows Installer service is properly registered.",
    1602: "The user cancels installation.",
    1603: "A fatal error occurred during installation.",
    1604: "Installation suspended, incomplete.",
    1605: "This action is only valid for products that are currently installed.",
    1606: "The feature identifier is not registered.",
    1607: "The component identifier is not registered.",
    1608: "This is an unknown property.",
    1609: "The handle is in an invalid state.",
    1610: "The configuration data for this product is corrupt. Contact your support personnel.",
    1611: "The component qualifier not present.",
    1612: "The installation source for this product is not available. Verify that the source exists and that you can access it.",
    1613: "This installation package cannot be installed by the Windows Installer service. You must install a Windows service pack that contains a newer version of the Windows Installer service.",
    1614: "The product is uninstalled.",
    1615: "The SQL query syntax is invalid or unsupported.",
    1616: "The record field does not exist.",
    1618: "Another installation is already in progress. Complete that installation before proceeding with this install.",
    1619: "This installation package could not be opened. Verify that the package exists and is accessible, or contact the application vendor to verify that this is a valid Windows Installer package.",
    1620: "This installation package could not be opened. Contact the application vendor to verify that this is a valid Windows Installer package.",
    1621: "There was an error starting the Windows Installer service user interface. Contact your support personnel.",
    1622: "There was an error opening installation log file. Verify that the specified log file location exists and is writable.",
    1623: "This language of this installation package is not supported by your system.",
    1624: "There was an error applying transforms. Verify that the specified transform paths are valid.",
    1625: "This installation is forbidden by system policy. Contact your system administrator.",
    1626: "The function could not be executed.",
    1627: "The function failed during execution.",
    1628: "An invalid or unknown table was specified.",
    1629: "The data supplied is the wrong type.",
    1630: "Data of this type is not supported.",
    1631: "The Windows Installer service failed to start. Contact your support personnel.",
    1632: "The Temp folder is either full or inaccessible. Verify that the Temp folder exists and that you can write to it.",
    1633: "This installation package is not supported on this platform. Contact your application vendor.",
    1634: "Component is not used on this machine.",
    1635: "This patch package could not be opened. Verify that the patch package exists and is accessible, or contact the application vendor to verify that this is a valid Windows Installer patch package.",
    1636: "This patch package could not be opened. Contact the application vendor to verify that this is a valid Windows Installer patch package.",
    1637: "This patch package cannot be processed by the Windows Installer service. You must install a Windows service pack that contains a newer version of the Windows Installer service.",
    1638: "Another version of this product is already installed. Installation of this version cannot continue. To configure or remove the existing version of this product, use Add/Remove Programs in Control Panel.",
    1639: "Invalid command line argument. Consult the Windows Installer SDK for detailed command-line help.",
    1640: "Installation from a Terminal Server client session is not permitted for the current user.",
    1641: "The installer has initiated a restart. This message is indicative of a success.",
    1642: "The installer cannot install the upgrade patch because the program being upgraded may be missing or the upgrade patch updates a different version of the program. Verify that the program to be upgraded exists on your computer and that you have the correct upgrade patch.",
    1643: "The patch package is not permitted by system policy.",
    1644: "One or more customizations are not permitted by system policy.",
    1645: "Windows Installer does not permit installation from a Remote Desktop Connection.",
    1646: "The patch package is not a removable patch package. Available beginning with Windows Installer version 3.0.",
    1647: "The patch is not applied to this product. Available beginning with Windows Installer version 3.0.",
    1648: "No valid sequence could be found for the set of patches. Available beginning with Windows Installer version 3.0.",
    1649: "Patch removal was disallowed by policy. Available beginning with Windows Installer version 3.0.",
    1650: "The XML patch data is invalid. Available beginning with Windows Installer version 3.0.",
    1651: "Administrative user failed to apply patch for a per-user managed or a per-machine application that is in advertise state. Available beginning with Windows Installer version 3.0.",
    3010: "A restart is required to complete the install. This message is indicative of a success. This does not include installs where the ForceReboot action is run."
}

upgrade_in_progress_msg = "Upgrade of Agent on host {host} is not yet completed and the host is still unmanageable."


def get_manual_upgrade_inst(exit_code, host):
    if exit_code in (16, 17):
        return manual_upgrade_inst % host + fail_reasons_list
    else:
        return manual_upgrade_inst % host


def get_path_module(host):
    if Const.isOsaWinPlatform(host.platform.os):
        return ntpath
    else:
        return posixpath


def get_remote_temp_dir(host):
    return get_path_module(host).join(host.rootpath, "tmp")


def get_remote_async_exec_path(host):
    return ntpath.join(get_remote_temp_dir(host), ASYNC_EXEC_FILENAME)


def get_remote_agent_rpm_path(host):
    return posixpath.join(get_remote_temp_dir(host), PAAGENT_RPM_NAME)


def schedule_update_windows_slave(task_item):
    # Preparing HCL request for scheduling agent upgrade via asyncExec.exe
    remote_temp_dir = get_remote_temp_dir(task_item.host)
    remote_async_exec_path = get_remote_async_exec_path(task_item.host)

    schedule_request = uHCL.Request(host_id=task_item.host.host_id, auto_export=True)
    schedule_request.mkdir(remote_temp_dir)
    schedule_request.fetch(
        srcfile=posixpath.basename(task_item.paagent_dist_url),
        urls=[posixpath.dirname(task_item.paagent_dist_url)],
        dstvar="archive"
    )
    schedule_request.extract("${archive}", remote_temp_dir)

    schedule_cmd_args = [
        remote_async_exec_path,
        '--delay 10',
        '--cluster',
        '--checkmutex {mutex}'.format(mutex=agent_msi_mutex),
        '--anchor {anchor}'.format(anchor=agent_anchor_name),
        '"{paagent_exe} /c /qn /l {update_log} REBOOT=Suppress AUTO_UPGRADE=1"'.format(
            paagent_exe=PAAGENT_EXE_FILENAME, update_log=WIN_UPGRADE_LOG)
    ]

    # With 'retvar' option we will catch return code and will not fail if it is not eq 0
    schedule_request.command(remote_async_exec_path, schedule_cmd_args, cwd=remote_temp_dir,
                             stderr="err", stdout="out", retvar="exit_code")

    uLogging.debug("Scheduling agent upgrade on Windows host {host}.".format(host=task_item.host))
    uLogging.debug("Executing {async_exec_launch}".format(async_exec_launch=" ".join(schedule_cmd_args)))
    schedule_result = schedule_request.performCompat()
    schedule_return_code = int(schedule_result['exit_code'])

    if schedule_return_code < 100:
        if schedule_return_code == 12:
            uLogging.info(
                "Agent upgrade on host {host} is running already. Skip scheduling.".format(host=task_item.host)
            )
        elif schedule_return_code != 0:
            err_msg = "Scheduling windows update on host {host} failed. AsyncExec exit code: {exit_code}; " \
                      "stdout: {out}; stderr: {err}".format(host=task_item.host, exit_code=schedule_result['exit_code'],
                                                            out=schedule_result['out'], err=schedule_result['err'])
            uLogging.err(err_msg)
            raise uUtil.ExecFailed(command=" ".join(schedule_cmd_args), status=schedule_result['exit_code'],
                                   out=schedule_result['out'], err=schedule_result['err'])


def handle_win_upgrade_failure_on_http(task_item, http_respond_out):
    op_error = uHCL.readHCLOperationError(http_respond_out)

    if op_error["code"] < 0:
        uLogging.debug("HCL operation result: \n{op_error}".format(op_error=pformat(op_error)))
        raise Exception(upgrade_in_progress_msg.format(host=task_item.host))
    else:
        uLogging.err("HTTP request failed. "
                     "Error code: {code}; message: {message}, type: {type}, module: {module}".format(
                        code=op_error["code"], message=op_error["message"], type=op_error["type"],
                        module=op_error["module"]))
        uLogging.err("Agent update on host {host} failed.\n{manual_upgrade_instruction}".format(
            host=task_item.host, manual_upgrade_instruction=get_manual_upgrade_inst(0, task_item.host)))
        raise Exception("Agent upgrade on host {host} failed. "
                        "Check error messages above.".format(host=task_item.host))


def handle_async_exec_error(exit_code, task_item, check_cmd_args, check_request_result):
    cluster_upgrade_err_pattern = re.compile("ERROR CODE: (.+)")
    cluster_upgrade_error_parsed = cluster_upgrade_err_pattern.search(check_request_result["out"])

    if cluster_upgrade_error_parsed is not None:
        app_code = int(cluster_upgrade_error_parsed.group(1))

        if app_code == 1604:
            uLogging.info("Agent already upgraded on host {host}".format(host=task_item.host))
        elif app_code == 3010:  # node needs to restart
            uLogging.info("Some files were locked during upgrade and a restart of node {host} is required "
                          "to complete the installation. \nWARNING: You can do it later "
                          "but before the next upgrade.".format(host=task_item.host))
        else:
            # try to interpret MSI code
            uLogging.err("Agent update on host {host} failed. MSI error: {error_description} ({error_id})."
                         "\n{manual_upgrade_instruction}".format(
                            host=task_item.host, error_description=msi_errors.get(app_code, '<unknown error>'),
                            error_id=app_code,
                            manual_upgrade_instruction=get_manual_upgrade_inst(exit_code, task_item.host)))
            raise uUtil.ExecFailed(command=" ".join(check_cmd_args), status=check_request_result['exit_code'],
                                   out=check_request_result['out'], err=check_request_result['err'])
    else:
        uLogging.err("Agent update on host {host} failed:\nUnknown Error\n{manual_upgrade_instruction}".format(
            host=task_item.host, manual_upgrade_instruction=get_manual_upgrade_inst(exit_code, task_item.host)))

        raise uUtil.ExecFailed(command=" ".join(check_cmd_args), status=check_request_result['exit_code'],
                               out=check_request_result['out'], err=check_request_result['err'])


def handle_cluster_upgrade_error(exit_code, task_item, check_cmd_args, check_request_result):
    uLogging.err("Cluster upgrade failed on host {host}".format(host=task_item.host))
    cluster_upgrade_err_pattern = re.compile(
        "ERROR CODE: ([-]*[\d]+).*ERROR: (.+)=== Cluster script log:(.+)=== End of cluster script log:",
        re.DOTALL)
    cluster_upgrade_error_parsed = cluster_upgrade_err_pattern.search(check_request_result["out"])

    if cluster_upgrade_error_parsed:
        uLogging.err("Script error code: {error_code}; error message: {error_message}; "
                     "cluster installation log: \n{cluster_script_log}".format(
                        error_code=cluster_upgrade_error_parsed.group(1),
                        error_message=cluster_upgrade_error_parsed.group(2),
                        cluster_script_log=cluster_upgrade_error_parsed.group(3)))
    else:
        uLogging.err("Error: {raw_output}".format(raw_output=check_request_result["out"]))

    uLogging.err("Agent update on host {host} failed. \n{manual_upgrade_instruction}".format(
        host=task_item.host, manual_upgrade_instruction=get_manual_upgrade_inst(exit_code, task_item.host)
    ))
    raise uUtil.ExecFailed(command=" ".join(check_cmd_args), status=check_request_result['exit_code'],
                           out=check_request_result['out'], err=check_request_result['err'])


def handle_win_upgrade_unknown_hcl_error(exit_code, task_item, check_cmd_args, check_request_result):
    uLogging.err("AsyncExec error detection failed. Exit code: {exit_code}; output: {raw_output}".format(
        exit_code=check_request_result["exit_code"], raw_output=check_request_result["out"]
    ))
    uLogging.err("Agent update on host {host} failed.\n{manual_upgrade_instruction}".format(
        host=task_item.host, manual_upgrade_instruction=get_manual_upgrade_inst(exit_code, task_item.host)
    ))
    raise uUtil.ExecFailed(command=" ".join(check_cmd_args), status=check_request_result['exit_code'],
                           out=check_request_result['out'], err=check_request_result['err'])


def handle_win_upgrade_failure_on_hcl(task_item, hcl_operation_result, check_cmd_args):
    uLogging.debug("AsyncExec passed, exit_code: {exit_code}".format(exit_code=hcl_operation_result["exit_code"]))
    exit_code = int(hcl_operation_result["exit_code"])

    if exit_code == 0:
        uLogging.debug("Agent on host {host} was successfully upgraded.".format(host=task_item.host))
    elif exit_code == 12:
        raise Exception(upgrade_in_progress_msg.format(host=task_item.host))
    elif exit_code == 16:  # ErrScript (cluster upgrade error)
        handle_cluster_upgrade_error(exit_code, task_item, check_cmd_args, hcl_operation_result)
    elif exit_code == 17:  # ErrApp
        # check application code (PAgent.exe)
        handle_async_exec_error(exit_code, task_item, check_cmd_args, hcl_operation_result)
    else:
        handle_win_upgrade_unknown_hcl_error(exit_code, task_item, check_cmd_args, hcl_operation_result)


def check_update_windows_slave(task_item, config):

    uLogging.debug("Checking if agent on Windows host {host} is updated".format(host=task_item.host))
    auth_token = uHCL.getHostAuthToken(task_item.host, config, config.mn_as_cert_issuer)
    remote_temp_dir = get_remote_temp_dir(task_item.host)
    remote_async_exec_path = get_remote_async_exec_path(task_item.host)

    # Asynchronous upgrade. If installation has been failed then PAgent.exe will be run again for product check only.
    # The following cases can be:
    #   1. exit code is 1604, it means installation is OK (manual upgrade is performed).
    #   2. exit code is 0 , it's OK too.
    #   3. exit code is 1603 (returned by bootstrapper when 'CheckWithoutUpgrade' built-in property
    #      is given at the command line. It means that agent not upgraded.

    check_result_request = uHCL.Request(host_id=task_item.host.host_id, auto_export=True)
    check_cmd_args = [remote_async_exec_path,
                      '--status',
                      '--anchor ' + agent_anchor_name,
                      '"{paagent_exe} /c /qn REBOOT=Suppress AUTO_UPGRADE=1 CheckWithoutRunUpgrade=1"'.format(
                          paagent_exe=PAAGENT_EXE_FILENAME
                      ),
                      '--exit-codes 0,1604']
    check_result_request.command(remote_async_exec_path, check_cmd_args, cwd=remote_temp_dir,
                                 stderr="err", stdout="out", retvar="exit_code")
    host_ip = uPEM.getHostCommunicationIP(task_item.host.host_id)
    check_result_http_request = urllib2.Request("https://{host_ip}:8352/process".format(host_ip=host_ip),
                                                headers={"Authorization": auth_token}, data=None)
    check_result_http_request.get_method = lambda: 'POST'
    uLogging.debug("Checking update status of Windows slave {host} via REST HCL request to {host_ip}".format(
        host=task_item.host, host_ip=host_ip))

    try:

        if uLinux.SSL_VERIFICATION_ENFORCED:
            http_respond = urllib2.urlopen(check_result_http_request, context=ssl._create_unverified_context(),
                                           data=check_result_request.toxml())
        else:
            http_respond = urllib2.urlopen(check_result_http_request, data=check_result_request.toxml())

        http_respond_out = http_respond.read()

        try:
            status_code = http_respond.getcode()
        except AttributeError:
            status_code = http_respond.code

    except urllib2.HTTPError, error:
        status_code = error.code
        http_respond_out = error.read()

    if status_code != 200:
        # Status != 200 means that we are not able to communicate with agent via XML RPC, agent was updated with error.
        handle_win_upgrade_failure_on_http(task_item, http_respond_out)
    else:
        # Status 200 means that we are able to communicate with agent via XML RPC, so agent certainly somehow updated,
        # and now we are checking how well it is was done (clusters, etc).
        # This scenario is actual not only for upgrade 7.0->7.1 (when agents protocol was changed), but also for
        # general health-check of agent after upgrade
        hcl_operation_result = uHCL.readHCLOperationResult(http_respond_out)
        handle_win_upgrade_failure_on_hcl(task_item, hcl_operation_result, check_cmd_args)
        return uHCL.readHCLOperationResult(http_respond_out)


def wait_for_linux_slave(task_item):
    uLogging.debug("Updated pa-agent on Linux host {host} is starting up, waiting it...".format(host=task_item.host))
    try:
        uPEM.ping(task_item.host.host_id)
    except Exception as e:

        if "Connection refused" in str(e):
            raise Exception("pa-agent service is not in operation after update on slave {host}".format(
                host=task_item.host))

        raise

def check_update_linux_slave(host, update_result):
    retcode_exist = 'retcode' in update_result
    successful_exit_code = retcode_exist and update_result['retcode'] == '0'
    failed_exit_code = retcode_exist and update_result['retcode'] != '0'
    already_up_to_date = failed_exit_code and 'does not update installed package' in update_result['stdout'] \
                         and 'Error: Nothing to do' in update_result['stderr']

    if not retcode_exist:
        uLogging.info("Successful update on slave {host}".format(host=host))
    elif successful_exit_code:
        uLogging.info("Successful update on slave {host}, "
                      "pa-agent service will be restarted asynchronously".format(host=host))
    elif already_up_to_date:
        uLogging.info("Successful update on slave {host}, pa-agent RPM of desired version "
                      "is already installed on target host, nothing to do, "
                      "HCL ping will check the operability".format(host=host))
    else:
        raise Exception("Update failed on slave {host}. Details: \n{update_result}".format(
            host=host, update_result=pformat(update_result)))


def update_slave(task_item, config):
    is_slave_updated = None

    try:
        if Const.isOsaWinPlatform(task_item.host.platform.os):
            if task_item.paagent_dist_url:
                schedule_update_windows_slave(task_item)
                uAction.ntimes_retried(check_update_windows_slave, 8, 30)(task_item, config)
                is_slave_updated = True
        else:
            linux_update_result = update_linux_slave(task_item, config)
            check_update_linux_slave(task_item.host, linux_update_result)

            # This is a workaround: see async restart code in pa-agent RPM
            async_upgrade_finished_sec = 11
            uLogging.debug("Waiting {async_upgrade_finished_sec} sec for agent upgrade process is finished "
                           "on host {host}".format(host=task_item.host,
                                                   async_upgrade_finished_sec=async_upgrade_finished_sec))
            sleep(async_upgrade_finished_sec)
            uAction.ntimes_retried(wait_for_linux_slave, 8, 30)(task_item)
            is_slave_updated = True

    except Exception as e:
        uLogging.warn("Error happen during upgrade slave {host}, check details in log or wait for moment when "
                      "the result will be processed".format(host=task_item.host))
        uLogging.save_traceback()
        raise e

    return is_slave_updated


def get_paagent_rpm_path(binfo, platform):
    key = ('pa-agent', platform.os, platform.osver)
    if key in binfo.rpms_to_update:
        uLogging.debug("Found agent for platform {platform}".format(platform=platform))
        r = binfo.rpms_to_update[key]
        return os.path.basename(r['path'])

    uLogging.debug("Agent for platform {platform} not found".format(platform=platform))
    return None


def get_paagent_exe_paths(binfo):
    """Returns uBuild.WindowsUpdate"""

    upd_kit = uBuild.WindowsUpdate()
    reversed_builds = list(reversed(binfo.builds))

    for build in reversed_builds:

        if upd_kit.async_exec_path is None and build.windows_update.async_exec_path is not None:
            upd_kit.async_exec_path = build.windows_update.async_exec_path
            uLogging.debug("Found asyncExec for Windows: {async_exec_path}".format(
                async_exec_path=upd_kit.async_exec_path)
            )

        if upd_kit.sn_installer_path is None and build.windows_update.sn_installer_path is not None:
            upd_kit.sn_installer_path = build.windows_update.sn_installer_path
            uLogging.debug("Found pa-agent for Windows: {sn_installer_path}".format(
                sn_installer_path=upd_kit.sn_installer_path)
            )

        if upd_kit.async_exec_path is not None and upd_kit.sn_installer_path is not None:
            uLogging.debug("Agent kit for Windows was found: {sn_installer}, {async_exec}".format(
                sn_installer=upd_kit.sn_installer_path, async_exec=upd_kit.async_exec_path))
            upd_kit.perform = True
            return upd_kit

    uLogging.debug("Cannot find agent or asyncExec for Windows")
    return upd_kit


def max_slave_upgrade_threads(hosts_to_upgrade_count, slave_upgrade_threads=None):
    max_limit = 50
    thread_count = int(hosts_to_upgrade_count)

    if thread_count > max_limit:
        # limiting with maximum
        thread_count = max_limit

    if slave_upgrade_threads:
        # rewriting if explicitly passed slave_upgrade_threads variable
        thread_count = slave_upgrade_threads

    uLogging.debug("Defined max parallel slave upgrade is {thread_count}".format(thread_count=thread_count))
    return thread_count


def is_slave_upgradable(host, binfo, config):
    uLogging.debug("Checking if slave {host} is upgradable".format(host=host))
    is_windows_host = Const.isOsaWinPlatform(host.platform.os)

    if host.host_id in binfo.progress.updated_hosts:
        uLogging.debug("Skipping already updated slave: {host}".format(host=host))
        return False

    if config.skip_win and is_windows_host:
        uLogging.debug("Skipping windows host {host} because was passed option '--skip:win'".format(host=host))
        return False

    if config.skip_rpms and not is_windows_host:
        uLogging.debug("Skipping Linux (RPM) host {host} because was passed option '--skip:rpms'".format(host=host))
        return False

    if not uPEM.canProceedWithHost(host):
        uLogging.warn("Skipping unavailable slave: {host}".format(host=host))
        return False

    # platform-specific URL for agent
    agent_url = prepare_paagent_url(host.platform, binfo, config)

    if not agent_url and is_windows_host:
        uLogging.debug("Skipping windows slave {host} as we have no pa-agent distrib "
                       "for its platform ({platform})".format(host=host, platform=host.platform))
        return False

    if not agent_url and not config.need_update_paagent and not config.need_update_yum_repourl:
        uLogging.debug("Skipping slave {host} as we have no pa-agent distrib for its platform ({platform}) "
                       "and updating YUM repourl is not needed also".format(host=host, platform=host.platform))
        return False

    uLogging.debug("Slave is upgradable: {host}".format(host=host))
    return True


ASYNC_EXEC_FILENAME = "AsyncExec.exe"
PAAGENT_EXE_FILENAME = "PAgent.exe"
PAAGENT_RPM_NAME = "pa-agent.rpm"
WIN_UPGRADE_LOG = "c:\\pemupgrade.log"


def prepare_paagent_rpm_url(platform, binfo, config):
    uLogging.debug("Building pa-agent upgrade kit for platform {platform}".format(platform=platform))
    agent_rpm_path = get_paagent_rpm_path(binfo, platform)

    if not agent_rpm_path:
        uLogging.debug("Agent for platform {platform} not found".format(platform=platform))
        return None

    corerpms_path = "corerpms/{distrib}{osver}".format(distrib=Const.getDistribLinDir(), osver=platform.osver)
    rpm_in_corerpms_path = posixpath.join(corerpms_path, os.path.basename(agent_rpm_path))

    # Here we could get URL to our RPM, but we need to prepare archive because 'fetch' HCL method can not recognize
    # something except gzip/bzip/exe. Need to simplify this after improving install.cpp from pa-agent project.
    # We need 'fetch' method as the unified transport for agents.

    local_path = uPackaging.getMainMirror().localpath  # /usr/local/pem/install/tarballs
    kit_dir_name = 'linux_agent_upgrade_kit'
    upd_path = os.path.join(local_path, kit_dir_name, config.update_name)
    kit_tarball_filename = '{platform}_{build_name}.tgz'.format(platform=platform, build_name=config.update_name)
    kit_tarball_full_path = os.path.join(upd_path, kit_tarball_filename)

    if not os.path.exists(upd_path):
        os.makedirs(upd_path)

    tgz = tarfile.open(kit_tarball_full_path, "w:gz")
    tgz.debug = 1
    tgz.add(os.path.join(local_path, rpm_in_corerpms_path), PAAGENT_RPM_NAME)
    tgz.close()
    uLogging.debug("pa-agent upgrade kit for platform {platform} has been built: {kit_tarball_full_path}".format(
        platform=platform, kit_tarball_full_path=kit_tarball_full_path))
    return 'http://{comm_ip}/tarballs/{kit_dir_name}/{update_name}/{kit_tarball_filename}'.format(
        comm_ip=config.communication_ip, kit_dir_name=kit_dir_name,
        update_name=config.update_name, kit_tarball_filename=kit_tarball_filename
    )


# This mutex is used by PEM MSI bootstrapper. We will do primary check for another copy of installer via this mutex.
agent_msi_mutex = "Global\\_MSISETUP_{2956EBA1-9B5A-4679-8618-357136DA66CA}"
agent_anchor_name = "pemagent_async_upgrade"


def prepare_paagent_exe_url(platform, binfo, config):
    uLogging.debug("Building pa-agent upgrade kit for platform {platform}".format(platform=platform))
    agent_kit = get_paagent_exe_paths(binfo)

    if not agent_kit.perform:
        uLogging.debug("Agent for platform {platform} not found".format(platform=platform))
        return None

    local_path = uPackaging.getMainMirror().localpath
    uPackaging.update_install_win_sn(agent_kit.sn_installer_path, local_path)
    kit_dir_name = 'windows_agent_upgrade_kit'
    kit_dir_path = os.path.join(local_path, kit_dir_name, config.update_name)

    if not os.path.exists(kit_dir_path):
        os.makedirs(kit_dir_path)

    kit_tarball_filename = '{platform}_{build_name}.tgz'.format(platform=platform, build_name=config.update_name)
    kit_tarball_full_path = os.path.join(kit_dir_path, kit_tarball_filename)

    tgz = tarfile.open(kit_tarball_full_path, "w:gz")
    tgz.debug = 1
    tgz.add(agent_kit.async_exec_path, ASYNC_EXEC_FILENAME)
    tgz.add(agent_kit.sn_installer_path, PAAGENT_EXE_FILENAME)
    tgz.close()

    uLogging.debug("pa-agent upgrade kit for platform {platform} has been built: {kit_tarball_full_path}".format(
        platform=platform, kit_tarball_full_path=kit_tarball_full_path))
    return 'http://{comm_ip}/tarballs/{kit_dir_name}/{update_name}/{kit_tarball_filename}'.format(
        comm_ip=config.communication_ip, kit_dir_name=kit_dir_name,
        update_name=config.update_name, kit_tarball_filename=kit_tarball_filename
    )


paagent_urls = {}


def prepare_paagent_url(platform, binfo, config):

    if platform not in paagent_urls:

        if Const.isOsaWinPlatform(platform.os):
            paagent_urls[platform] = prepare_paagent_exe_url(platform, binfo, config)
        else:
            paagent_urls[platform] = prepare_paagent_rpm_url(platform, binfo, config)

        uLogging.debug("Defined pa-agent URL for platform {platform} is {url}".format(
            platform=platform, url=paagent_urls[platform]
        ))

    return paagent_urls[platform]


def slave_upgrade_paagent_and_repourl(binfo, config):
    """Upgrade pa-agent on all slaves

    Parameters:
        :param binfo: uDLModel.BuildInfo
        :param config: uConfig.Config
    """

    uLogging.debug("Preparing to update agent on slaves")
    upgrade_paagent_and_repourl(binfo, config, uPEM.get_hosts_with_agent())


def is_need_to_update_paagent(binfo):
    # Checking available pa-agent RPM in build. We assume if there is new RPM, there is new EXE also.
    return bool([rpm for rpm in binfo.upgrade_instructions.native_packages if 'pa-agent' in rpm.name])


def upgrade_paagent_and_repourl(binfo, config, slave_hosts):
    config.need_update_paagent = is_need_to_update_paagent(binfo)
    
    if not config.need_update_paagent and not config.need_update_yum_repourl:
        uLogging.info("No new agent RPMs in build, updating YUM repo URL is not needed also, skipping agent update.")
        return

    uLogging.debug(
        "Need update YUM repo URL: {need_update_yum_repourl}; "
        "there are new agents in build: {need_update_paagent}".format(
            need_update_yum_repourl=config.need_update_yum_repourl, need_update_paagent=config.need_update_paagent))

    uAction.progress.do("Updating agents on slave nodes")
    config.mn_as_cert_issuer = uHCL.getHostCertificateDigest(uPEM.getHost(1))

    # Filtering out non-upgradable slaves
    slaves = [host for host in slave_hosts if host.host_id != 1]
    uLogging.debug("Found slaves with agent: \n{slaves}".format(slaves=pformat(slaves)))
    slaves = filter(lambda slave: is_slave_upgradable(slave, binfo, config), slaves)
    uLogging.debug("All non-upgradable slaves are filtered out, actual slave-to-upgrade list now: "
                   "\n{slaves}".format(slaves=pformat(slaves)))

    if not slaves:
        uLogging.info("There is no slaves marked for update.")
        uAction.progress.done()
        return

    # Preparing task pool for updating.
    pool = preparePool(config)
    slave_upgrade_monitoring = SlaveUpgradeMonitoring(pool, binfo, slaves)

    # Filling task pool for slaves
    for host in slaves:
        try:
            # Defining paagent url. If this will be eq None, package will not be updated
            paagent_url = prepare_paagent_url(host.platform, binfo, config)
            uLogging.debug("Slave '{host}' upgrade scheduled. Pa-agent URL is: '{agent_url}'"
                           .format(host=host, agent_url=paagent_url))
            pool.put(TaskItem(host, paagent_url))
        except uAction.ActionIgnored:
            continue

    thread_count = max_slave_upgrade_threads(hosts_to_upgrade_count=len(slaves),
                                             slave_upgrade_threads=config.slave_upgrade_threads)

    try:
        pool.start(thread_count)
        slave_upgrade_monitoring.start()
        uLogging.info("Upgrade for agents on slaves started (parallel: {thread_count})".format(
            thread_count=thread_count))
        uAction.retriable(process_pool_results)(pool, binfo, config)
        uLogging.info("All results of upgrading agents on slaves processed. ")
        report_skipped_hosts(binfo)
    except (Exception, KeyboardInterrupt) as e:
        # to remember and raise what is happened under try statement if finally statement has failures too
        uLogging.save_traceback()
        pool.terminateLocked()
        raise e
    finally:
        pool.terminate()
        slave_upgrade_monitoring.terminate()
        uAction.progress.done()

upgrade_status_changed_event = threading.Event()


class SlaveUpgradeMonitoring(threading.Thread):
    def __init__(self, pool, binfo, slaves):
        super(self.__class__, self).__init__()
        self.pool = pool
        self.binfo = binfo
        self.slaves = slaves
        self.need_terminate = threading.Event()

    def trigger_report(self):
        report_slave_upgrade_status(self.binfo, self.pool, len(self.slaves))

    def run(self):
        uLogging.debug("Starting monitoring for slave upgrade process")
        upgrade_status_changed_event.clear()

        while True:
            upgrade_status_changed_event.wait(30.0)

            if self.need_terminate.is_set():
                upgrade_status_changed_event.clear()
                break

            self.trigger_report()
            upgrade_status_changed_event.clear()

    def terminate(self):
        uLogging.debug("Terminating monitoring for slave upgrade process")
        self.need_terminate.set()

        if self.is_alive():
            upgrade_status_changed_event.set()
            self.join(30.0)

        uLogging.debug("Monitoring for slave upgrade process is terminated")


def report_skipped_hosts(binfo):
    if binfo.progress.failed_hosts:
        uLogging.warn("For some slave nodes ({items_count} items) upgrade was skipped, "
                      "please upgrade pa-agent manually.".format(items_count=len(binfo.progress.failed_hosts)))
        uLogging.warn("Skipped slaves list:\n{slave_list}".format(
            slave_list="\n".join([str(x.host) for x in binfo.progress.failed_hosts])))
        uLogging.warn("Detailed info about skipped slaves below (per host)")

        for failed_slave_upgrade in binfo.progress.failed_hosts:
            uLogging.warn("Host: {host}; details: \n{details}".format(
                host=failed_slave_upgrade.host, details=failed_slave_upgrade.error))


__all__ = ["slave_upgrade_paagent_and_repourl", "report_skipped_hosts"]
