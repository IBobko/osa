
There are unfinished transactions remaining. You might consider running yum-complete-transaction, or "yum-complete-transaction --cleanup-only" and "yum history redo last", first to finish them. If those don't work you'll have to try removing/installing packages by hand (maybe package-cleanup can help).


export NEXUS_URL=http://ci.int.zone
export SITE_BINREPO=http://binrepo.int.zone
export JAVA_HOME="/usr/java/jdk1.8.0_151"
export MVN_HOME="/usr/apache-maven-3.2.5"
export PATH="${JAVA_HOME}/bin:${MVN_HOME}/bin:${PATH}"
export PCV=local
export BSSCV=local
export DOMAINCV=local
export JOBS=12




sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

# Billing HOWTO
https://confluence.int.zone/pages/viewpage.action?pageId=920599603



docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --dns 10.194.4.3 --dns 10.194.4.4 --kernel-memory 6g --cpus 6 -v /sys/fs/cgroup:/sys/fs/cgroup:ro --privileged ingram:2.0


docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --dns 10.194.4.3 --dns 10.194.4.4 --kernel-memory 6g --oom-kill-disable ingram:2.0

docker run -e DISPLAY="172.17.0.1$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix --dns 10.194.4.3 --dns 10.194.4.4 ingram:2.0

sudo docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v /run/dbus:/run/dbus ingram:2.1

sudo docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --dns 10.194.4.3 --dns 10.194.4.4 -v /run/dbus:/run/dbus ingram:2.0



sudo docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix --dns 10.194.4.3 --dns 10.194.4.4 -v /run/dbus:/run/dbus ingram:2.1

docker rm $(docker ps -f "ancestor=ingram" -a -q)

# Пересборка УАМ



DOCKER_ENGINE=172.17.0.1 mvn clean install deploy -P DOCKER_BUILD -Dauto=54-igor -Ddocker.username=platform -Ddocker.password=1q2w3e



helm repo update
helm del --purge uam
helm del --purge uam-db
helm install a8n/postgresql --name uam-db --wait --timeout 240 --debug --set postgresUser=uam,postgresPassword=1q2w3e,postgresDatabase=onboard,persistence.enabled=false
export POSTGRES_PASSWORD=$(kubectl get secret --namespace default uam-db-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)
helm install a8n/uam --name uam --set devmode.enabled=true --set oauthkey=`uuidgen` --set oauthsecret=`uuidgen` --set dsdbname=postgres --set dslogin=postgres --set dspassword=`echo -n ${POSTGRES_PASSWORD}| base64` --set dshost=uam-db-postgresql



helm repo update
helm upgrade uam a8n/uam --version 1.2.258-igor-2 --reuse-values

export MN_HOST=POAMN-62cf1d7ec9bc.aqa.int.zone
ssh -L 8787:uam-debug:8787 root@$MN_HOST

docker run --rm -it -e RUNNER_OPTS="-DstackName=igor-uam" -v /etc/resolv.conf:/etc/resolv.conf -e cucumber.options='classpath:features/account/ux1/uninitialized_reseller.feature' platform.repo.int.zone/automation/e2e-tests-v2-mvn-runner:20.5.0.259


mvn test -e -B -DstackName=igor-idp -Dcucumber.options='classpath:features/customers/customer_management.feature' -Dcoverage=0 -DforkCount=0


customer_management.feature

# layout poa
grep -r "field: 'paAccount.adminContact.email'," .


ls -la $(grep -r "Customer list must be formatted as XLSX file." . -l)




helm install a8n/idp-backend --name idp-backend --wait --timeout 600 --set oauthkey=`uuidgen`,oauthsecret=`uuidgen`,dockerrepo=a8n-docker.repo.int.zone,dslogin=postgresql,dspassword=`echo -n 1q2w3e| base64`,dsdbname=a8n-idp,dshost=postgres-postgresql,jbossadminpassword=1q2w3e4@,jdbcconnectionparams='?ssl=require&ApplicationName=a8n-idp'






\cp /etc/resolv.conf ~/resolv.conf
sed -i 's/nameserver 192.168.1.254/nameserver 10.194.4.3\nnameserver 10.194.4.4\nnameserver 192.168.1.254/' ~/resolv.conf
\cp -f ~/resolv.conf /etc/resolv.conf
rm  -f ~/resolv.conf
exit



\cp /run/systemd/resolve/resolv.conf ~/resolv.conf
sed -i 's/nameserver 192.168.1.254/nameserver 10.194.4.3\nnameserver 10.194.4.4\nnameserver 192.168.1.254/' ~/resolv.conf
echo 1 | sudo -S ls
sudo \cp -f ~/resolv.conf /run/systemd/resolve/resolv.conf
rm  -f ~/resolv.conf



sed -i 's/DEBUG_MODE="${DEBUG:-false}"/DEBUG_MODE="${DEBUG:-true}"/' /usr/local/pem/wildfly-16.0.0.Final/bin/standalone.sh
sed -i 's/address=$DEBUG_PORT/address=*:$DEBUG_PORT/' /usr/local/pem/wildfly-16.0.0.Final/bin/standalone.sh
systemctl daemon-reload
/usr/local/pem/wildfly-16.0.0.Final/bin/add-user.sh  --user root --password 1
service pau restart




curl 'https://aylzi.brnd8cb7f8a3-6ff146.aqa.int.zone/aps/2/resources/6d22d77d-d518-482a-924f-a9c9c28c2aed/captcha' \
  -H 'Connection: keep-alive' \
  -H 'Pragma: no-cache' \
  -H 'Cache-Control: no-cache' \
  -H 'X-Correlation-ID: c7e08d87-3d3d-ed92-a54e-15e5e4aff075' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'APS-Token: JEFFUy0xMjgtR0NNJEx5U29NZnhSeDEyT3VRR0gkYlVoK1VSY1VCUUxYMWYyVVlYY0s4WUJLd1RrUHZDWDBDWWhKeTVuRnlWYmFKdnhwcUJGb2VzeUxBK1FPYlhVMDlBTmQzTTlJaHRLdUpaSlUzTXBJVUtHRDNwZmNkZmdzS0dXT0tkbXp6aXlJUGpqMXNoRVd1WnNBbTdoa1pCN3M3K0RyNlpLWEhUbllIblZZKzY0QU8rU3BnWlR1a2Vzb2MyUEdGZEpyQ3c2V0JvcmxtMTJTR21kUGY4ZFU2TU1Dcktzb0Y4TUMwWTNhYk44U1h5MmZWL0pPQkJFYWZJaU0wcHZRU0ErNmhiWndoVkJSdStxQStJZjFnWUxkZnVBRGY5ajN5OGt5dUs5c3hFOE5ZTFZHbFpoZHdVWTFjNEJQWDRpZDdUZElzajlSZHN1NHRkWE9JYm0zd1BWcUhHdFlFUUFOUktMdUJlRndoUFVCWWRnNVFXc2hRSjJwM3dITlozaWRiYTRxSjUrZ205eFp6U3NGalRvQXNhY2x5anZtRnh2eG5yVVFsV0EzUVN0MlhUNzJtcmpUUnZOOUtFVFlNQVNUOXhhQXFseThuVEh2RVZVaXE2UU53bUVIWXZzS2VWS2RaT0tBT2c9PQ==' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36' \
  -H 'APS-Locale: en_US' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Accept: */*' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Referer: https://aylzi.brnd8cb7f8a3-6ff146.aqa.int.zone/aps/2/packages/c9eadb89-f24a-481c-a179-97eac824ea8a/ui/bootstrapApp.html?apsUIRuntimeVersion=2.12-48&appId=http%3A%2F%2Fcloudblue.com%2Fuam&parentOrigin=https%3A%2F%2Faylzi.brnd8cb7f8a3-6ff146.aqa.int.zone' \
  -H 'Accept-Language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7' \
  -H 'Cookie: _ga=GA1.2.328780167.1592493749; _gid=GA1.2.481454216.1593082828; JSESSIONID=EjPLMcJ1P4jMa8KK8dt1paWU31ukFY1_FPgyCIHK.10.26.155.202' \
  --compressed \
  --insecure



curl "http://poamn-aba739248fcd.aqa.int.zone:8080/aps/2/resources?implementing(http://www.parallels.com/pa/pa-core-services/branding-management/1.1)" \
-H "APS-TOKEN: JEFFUy0xMjgtR0NNJGJ2OTdmOTEwV3U4TCtDRGskRWs5V3NNaWhScnRHRURNZ1QxU1pjbGZ6L0ZjeEZRQVJIZGx1YU1EZDczclZlNFFkU1VzL2hUTWRyb2liNnhMRnhoSlAxMmhoMmgrQmFjc3dOeW5FaFA3aUpuTUxmTWtUSi9VcVFEbnV2dGdtaEFHdHU1eDNTb2dUb3VNaXVBd3RqbWIrK1NOVWxuRWlQQkoxa3pyTzlBaThMSTRiUFNvY1lrQkJvWWJGUDh5T2pjZ0ZzK2tYaTlINWpWVHp0NEVHbGpDSExkNXl4aGM1UGpMcTM1V0lRTko0Z085bGJpcHBPQzZzLzE1dGwrZ0ZCVHVpaXd0SFZUakVkeFRHZXBtaE5xdFhydWY5YXg0YzVjdW43QnVHaHZQb0xXZEpDNkE2WHdrd2tSNWNBWkh1TlFmV0ZjUGZzUzlaOUtoTlloMUdXbGtXd2ZOUFNERXZZazJrOFk1S2lKSGlrMjBmUjBHOW1PYm5oS0wybkdKOWtWWVJ6YzJzNnVKbVltd1F1RmNOWURFcmNKT0trbldIUmc3aEo0Qk1Nbk5ONzI3anNmNG1jT3ZjVXN3cTVzTE92cEM2VmRxVHJQUXdESmdjOENvUDVBRzdoWXY2bGVTdnFsZzFoM0ZqVTB4S2x6RUhqZ08zQitNNjdFZE5xSVYxanRyNFRiZWduRG5XSEYzTVl6eW83OGdj"

GET http://poamn-aba739248fcd.aqa.int.zone:8080/aps/2/resources??implementing(http://www.parallels.com/pa/pa-core-services/branding-management/1.1)
APS-TOKEN:JEFFUy0xMjgtR0NNJGdrQVQwTGs2T2pUbkYwZlgkN1M3ZU4vSFViN3orNzVFbnE4dERVWTc5OTZNenBub2MvVmxQUjl0TTVwbDNPb2Raa25QYnFxek5Cd09WRWFhZi8wY0NETGo0bG1NL2p0L3FaNlZDT3BmVkdMQW4vbHNBQjU4WmxPakV4NElzWEhaVlo1Y013R1E0U3l4VUVVK1BkWE9sdWNHWmpCa0ZyeHJrcTJad1NzM2lKR0hML05WU2N0YVEwM2xuRWU2ZkRodm5CYXlSVHRueTZGMWFjdWY3NVJrMTB4NTdGOTRmZVZmVmN5VkQvRUZWd2ZtNjVvVUxQNFJINXhNVmFZSzJmY1drejUzVlE1NlVia3M0Qks3VWNhUUxtSTZXRVhlQVhjcEVmcHppTVFUSzdlb0daTG5PN0xwdDIxeGhSekZXbHJ1ZXA1ak9HaWRET2FETHBoN0hxLzJnRStTWitDaU5oclRJVjhUSzB3NlNERjl5VXNOUy8rV1d2Ny9odHFxTjJrNUJ3KzRqNzYwN25JQzBDVitSY0t5ZVkyZ3h5R2h4dU53N1MvcnFTcU5Hc05nZXNtTjlOaDdIT1ZYY0Z1MUY0b2JZUFNhRFNHSTBQR2JsQlN4Zm84bkxoTDBEQkxUNThJOUp0VzE0bW1xNUF1K3ZYa3lPbGUyVXF0L0xpb3paRFYyNjdNaHJ3TmYvekZBbUdaOFpocG1r






yum -y install \
    gettext rpm-build bison flex openldap-devel gcc-c++ libbuild-devel\

    libuuid-devel quota-devel glib2-devel protobuf-devel libselinux-utils\

    libevent-devel postgresql-devel mariadb-devel libev-devel php-cli\

    php-xml apr-devel openssl sudo libxml2 libxml2-devel\

    libxml++ libxml++-devel postgresql96-devel boost-devel\

    xerces-c-devel libcurl-devel gnutls gnutls-devel\

    liblockfile liblockfile-devel redhat-rpm-config \

    unixODBC  unixODBC-devel  libicu-devel \

    gpgme-devel  GeoIP-devel  perl-Config-General  perl-ExtUtils-MakeMaker \

    perl-DBI  perl-Time-HiRes  perl-XML-Simple  perl-IO-Zlib \

    bzip2-devel  php  python-netaddr  xorg-x11-server-Xvfb\

    libarchive-devel  libarchive  bzip2-libs  libzip  libssh2-devel  libidn-devel  libcap-devel





    echo -n | openssl s_client -connect HOST:PORTNUMBER \
    | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > /tmp/$SERVERNAME.cert




rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/gsoap-2.8.17-2.pem.el7.x86_64.rpm
rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/bin2c-1.1-0.el7.x86_64.rpm
rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/poco-1.6.1-1.pem.el7.x86_64.rpm
rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/poco-devel-1.6.1-1.pem.el7.x86_64.rpm
rpm -ivh https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-centos96-9.6-3.noarch.rpm
rpm -ivh http://binrepo.int.zone/pba/aps/aps-php-runtime-2.2-49.noarch.rpm
rpm -ivh http://binrepo.int.zone/pba/aps/apstools-2.2-282.noarch.rpm
rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/postgresql96-libs-9.6.2-1PGDG.rhel7.x86_64.rpm
rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/postgresql96-9.6.2-1PGDG.rhel7.x86_64.rpm
rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/postgresql96-server-9.6.2-1PGDG.rhel7.x86_64.rpm
rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/postgresql96-devel-9.6.2-1PGDG.rhel7.x86_64.rpm
rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/libetpan-1.7.2-2.el7.centos.x86_64.rpm
rpm -ivh http://binrepo.int.zone/RPMS/RHEL/7/libetpan-devel-1.7.2-2.el7.centos.x86_64.rpm
rpm -ivh http://deliver.int.zone/oa/7.4/repo/RHEL/7/libiqxmlrpc-0.13.6-59.parallels.x86_64.rpm





sudo docker exec -it e4f0e5d1be8e /bin/bash
rm -rf /root/IdeaProjects/idea_plugin



sudo docker run --rm -it -p 8001:8000 -e RUNNER_OPTS="-Dspconfig.address=spconfig.int.zone -DstackName=igor-platform-uam" -e cucumber.options='classpath:features/account/ux1/uninitialized_reseller.feature' platform.repo.int.zone/automation/e2e-tests-v2-mvn-runner:8.4.0.795








sudo docker run --rm -it  -v /root/uam/e2e-tests-v2/uam-e2e-tests-v2/src/main/resources/features/:/e2e/features -v /root/automation-20.4/poa/e2e-tests-v2/sdk-e2e-tests-v2-assembly/target:/e2e/target -e RUNNER_OPTS="-DstackName=oa_204_master_uam_igor" -e cucumber.options='/e2e/features/reseller_management.feature' platform.repo.int.zone/automation/e2e-tests-v2-mvn-runner:20.4.0.1125_KB201012-2069
















https://XDmvQ.brnd01b161a0-6df413.aqa.int.zone/onboard1000015





