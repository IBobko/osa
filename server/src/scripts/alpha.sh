


export MN_HOST=POAMN-fd77f32e3ab1.aqa.int.zone
scp /root/IdeaProjects/osa/modules/billing/BSS/bss-war/target/bss-war.war root@$MN_HOST:/root && ssh root@$MN_HOST "time sh /usr/local/pem/wildfly-16.0.0.Final/bin/jboss-cli.sh --connect deploy\ -f\ /root/bss-war.war"



# Demo stand POAMN-6d6e6fde3dba.aqa.int.zone

ilya.martynov@ingrammicro.com
1q2w3e!Q@W#E

https://demo.ap.int.zone


saleAndBranchIdsValidatorBean


export PCV=local
mvn install -f modules/platform
​

export MN_HOST=POAMN-626bafe306c1.aqa.int.zone
mvn install -f modules/billing/BSS/bsskernel-ejb -DskipTests &&  mvn install -f modules/billing/BSS/bss-war -DskipTests
scp /root/IdeaProjects/osa/modules/billing/BSS/bss-war/target/bss-war.war root@$MN_HOST:/root/ && ssh root@$MN_HOST "sh /usr/local/pem/wildfly-16.0.0.Final/bin/jboss-cli.sh --connect -u=root -p=1  deploy\ -f\ /root/bss-war.war"




# Дистрибутивы
http://deliver.int.zone/cb/20.5/dist/

#Start e2e test for IDP
mvnDebug install -e -B -DstackName=igor-platform-idp-2 -Dspconfig.address=spconfig.int.zone -Dcucumber.options='classpath:features/token.feature' -Dcoverage=0 -DforkCount=0 -Dremote=http://localhost:4444/wd/hub


mvn install -e -B -DstackName=igor-platform-idp-3 -Dspconfig.address=spconfig.int.zone -Dcucumber.options='classpath:features/qa/single_login_form.feature' -Dcoverage=0 -DforkCount=0 -Dremote=http://localhost:4444/wd/hub

mvnDebug install -e -B -DstackName=igor-platform-idp-2 -Dspconfig.address=spconfig.int.zone -Dcucumber.options='classpath:features/qa/single_login_form.feature' -Dcoverage=0 -DforkCount=0 -Dremote=http://localhost:4444/wd/hub

# Start Selenium docker
docker run --rm -ti --name=grid -p 4444:24444 -p 5900:25900 --shm-size=1g -p 6080:26080 -e NOVNC=true -e VNC_PASSWORD=no -e MAX_INSTANCES=200 -e MAX_SESSIONS=200  elgalu/selenium:3.141.59-p26
docker run --rm -ti --name=grid -p 4444:24444 -p 5900:25900 --shm-size=1g -p 6080:26080 -e NOVNC=true -e VNC_PASSWORD=no -e MAX_INSTANCES=200 -e MAX_SESSIONS=200  elgalu/selenium:3.141.59-p17



https://confluence.int.zone/display/PLATFORM/IDP+developer+regular+tasks


#Deploy IDP
export MN_HOST=POAMN-fd77f32e3ab1.aqa.int.zone
mvn package -f backend/ && scp ./backend/target/idp-backend.war root@$MN_HOST:/root/ && ssh root@$MN_HOST "sh /usr/local/pem/wildfly-16.0.0.Final/bin/jboss-cli.sh --connect --controller=idp-jboss-admin -u=admin -p=$IDP_JBOSS_PASSWORD  deploy\ -f\ /root/idp-backend.war"


1.7.10000
# IDP-EJB
export MN_HOST=POAMN-9f54412b7eaa.aqa.int.zone
export AUTO=д
mvn clean install -f ./modules/platform/u/EAR/idp-ejb -Dauto=${AUTO} && mvn clean install -f ./modules/platform/u/EAR/core-war -Dauto=${AUTO}  && mvn clean install -f ./modules/platform/u/EAR/core-ear -Dauto=${AUTO}  && scp ./modules/platform/u/EAR/core-ear/target/core-ear.ear root@$MN_HOST:/root/ && ssh root@$MN_HOST "sh /usr/local/pem/wildfly-16.0.0.Final/bin/jboss-cli.sh --connect -u=root -p=1  deploy\ -f\ /root/core-ear.ear"




export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export PATH=${PATH}:${JAVA_HOME}/bin

export MN_HOST=POAMN-d0d9d8b1078b.aqa.int.zone
export AUTO=490
mvn clean install -f ./modules/platform/u/EAR/branding-ejb -Dauto=${AUTO} && mvn clean install -f ./modules/platform/u/EAR/core-war -Dauto=${AUTO}  && mvn clean install -f ./modules/platform/u/EAR/core-ear -Dauto=${AUTO}  && scp ./modules/platform/u/EAR/core-ear/target/core-ear.ear root@$MN_HOST:/root/ && ssh root@$MN_HOST "sh /usr/local/pem/wildfly-16.0.0.Final/bin/jboss-cli.sh --connect -u=root -p=1  deploy\ -f\ /root/core-ear.ear"



export MN_HOST=POAMN-2ff482754159.aqa.int.zone
ssh -L 8787:uam-debug:8787 root@$MN_HOST



export MN_HOST=POAMN-0ef51a93a4d1.aqa.int.zone
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export PATH=${PATH}:${JAVA_HOME}/bin
export AUTO=8009
export DOCKER_HOST=10.192.38.77 && mvn clean install -f backend/ -Dauto=$AUTO && mvn clean install -f keycloak/ -Dauto=$AUTO && mvn clean install -f application/ -Dauto=$AUTO && mvn deploy -DDOCKER_ENGINE=10.192.38.77 -Ddocker.username=platform -Ddocker.password=1q2w3e -Dauto=$AUTO -f helm/


export AUTO=igor-1
mvn clean install -Dauto=$AUTO && mvn deploy -DDOCKER_ENGINE=172.17.0.1 -Ddocker.username=platform -Ddocker.password=1q2w3e -Dauto=$AUTO -f helm/


export MN_HOST=POAMN-0ef51a93a4d1.aqa.int.zone



sudo docker run --rm -it -p 8001:8000 -e RUNNER_OPTS="-Dspconfig.address=spconfig.int.zone -DstackName=igor-platform-uam" -e cucumber.options='classpath:features/account/ux1/uninitialized_reseller.feature' platform.repo.int.zone/automation/e2e-tests-v2-mvn-runner:8.4.0.795


#idp-backend
dockerrepo: skeleton.repo.int.zone
dsdbname: idpdb
dshost: postgres-postgresql.default.svc.cluster.local
dslogin: DSLOGIN
dspassword: RFNQQVNTV09SRA==
dsport: 5432
jbossadminpassword: 1q2w3e4@
jdbcconnectionparams: ?ApplicationName=idp-app
maxdbpoolsize: 16
mindbpoolsize: 1
oauthkey: 3f82119e-d87b-11e8-9f8b-f2801f1b9fd1
oauthsecret: 3f821428-d87b-11e8-9f8b-f2801f1b9fd1


# postgres
persistence:
  enabled: false
postgresDatabase: idpdb
postgresPassword: DSPASSWORD
postgresUser: DSLOGIN



export MN_HOST=POAMN-0ef51a93a4d1.aqa.int.zone


mvn verify -DDOCKER_ENGINE=10.192.38.77 -f backend/ -Dit.test=com.odin.idp.IDPBackendIT#checkGlobalConfiguration



sudo docker run -i -t -p 8888:8888 continuumio/miniconda3 /bin/bash -c "/opt/conda/bin/conda install jupyter -y --quiet && mkdir /opt/notebooks && /opt/conda/bin/jupyter notebook --notebook-dir=/opt/notebooks --ip='*' --port=8888 --no-browser --allow-root"



sudo docker run --rm -it -p 8001:8000 -v /home/ibobko/Work/ssh/osa/modules/platform/e2e-tests-v2/account-e2e-tests-v2/target:/e2e/target -v /home/ibobko/Work/1:/e2e/build -e RUNNER_OPTS="-Dspconfig.address=spconfig.int.zone -DstackName=igor-platform-idp-2" -e cucumber.options='classpath:features/account/ux1/uninitialized_reseller.feature' platform.repo.int.zone/automation/e2e-tests-v2-mvn-runner:8.4.0.795


sudo docker run --rm -it -e RUNNER_OPTS="-DstackName=igor-uam" -e cucumber.options='classpath:features/account/ux1/uninitialized_reseller.feature' platform.repo.int.zone/automation/e2e-tests-v2-mvn-runner:20.5.0.353



Перед тем как сделать слепок стеки, нужно
 - Обновить в этом файле хэш стеки.
 - Обновить в дебагере ИДЕЕ.
 - Залить туда ключ SSH. (KuMasterService, PlatformService)
 - Обновить время на KuMasterService и PlatformService (Установить ntp, сделать апдейт)
 - Включить дебаг на платформе.
 - Создать пользователя root:1 через add-user.sh
 - Добавить туда реселеров
 - Обновить IDP
 - Поставить UAM

 systemctl daemon-reload


yum -y install ntp ntpdate
systemctl start ntpd
systemctl enable ntpd
ntpdate -u -s 0.centos.pool.ntp.org 1.centos.pool.ntp.org 2.centos.pool.ntp.org
date

hFz2XWdikU




michael.oreilly5923@POAMN-554a6900c0f5.aqa.int.zone
q_u23cgE


store2apiuser1000001


export MN_HOST=POAMN-0ef51a93a4d1.aqa.int.zone
ssh -L 0.0.0.0:8788:idp-jboss-admin:8787 root@$MN_HOST


export MN_HOST=POAMN-0ef51a93a4d1.aqa.int.zone
ssh -L 8788:idp-debug:8787 root@$MN_HOST


## Returns all available versions
helm search -l idp-backend



helm get values postgres > pg_val.yaml
helm get values idp-backend > idp_val.yaml
helm delete --purge idp-backend
helm delete --purge postgres
helm repo update
helm install a8n/postgresql --values pg_val.yaml --name postgres --timeout 240 --wait

# Insert needed version
helm install a8n/idp-backend --name idp-backend --values idp_val.yaml --version "1.7.91"
kubectl get pods




helm get values idp-backend > idp_val.yaml
helm delete --purge idp-backend
helm repo update
# Insert needed version
helm install a8n.idp-backend --name idp-backend --values idp_val.yaml --version "1.4.8023"
kubectl get pods




helm repo update
helm upgrade idp-backend a8n-skeleton/idp-backend  --version "1.7.10006"
kubectl get pods




docker-ubuntu-vnc-desktop


export MN_HOST=POAMN-63446958ae80.aqa.int.zone
export IDP_JBOSS_PASSWORD=1q2w3e4@
mvn install -f keycloak/spi && scp keycloak/spi/spi-ear/target/spi-ear.ear root@$MN_HOST:/root/ && ssh root@$MN_HOST "sh /usr/local/pem/wildfly-16.0.0.Final/bin/jboss-cli.sh --connect --controller=idp-jboss-admin -u=admin -p=$IDP_JBOSS_PASSWORD  deploy\ -f\ /root/spi-ear.ear"


Login into CCPv2 by url https://WMZjh.brnd85c038ab-53682c.aqa.int.zone using login: emily.halvorson5152@POAMN-7ee2e52e39ae.aqa.int.zone and password: 1q2w3e!Q@W#E


Login into CCPv2 by url https://SjVfA.brndf9859ad1-464750.aqa.int.zone using login: emily.shanahan2206@POAMN-8ef1a69c7846.aqa.int.zone and password: 1q2w3e!Q@W#E



emily.rice6611@POAMN-8ef1a69c7846.aqa.int.zone

https://tiqke.brndf9859ad1-464750.aqa.int.zone/auth/realms/sr4/protocol/openid-connect/auth?response_type=code&redirect_uri=https%3A%2F%2Ftiqke.brndf9859ad1-464750.aqa.int.zone%2Fsp%2Fcallback%2F%3Fclient_name%3Dsr4&state=gtr2ywKUvPHPykarmPE3pGQ7XLFmN8TPC0-d0mqBFkM&client_id=oss&scope=openid+profile+email


untilfail() {
    for i in {0..1000}
    do
       echo "Running $i"
       $@
       if [[ "$?" -ne 0 ]]; then
         echo "Failed $i"
         break
       fi
       echo "Success $i"
    done
}



curl -X PUT http://poamn-0ef51a93a4d1.aqa.int.zone:8080/aps/2/resources/de6eaae8-a766-43c4-b8c3-c3a2b24ca33c/migrate/user/8 -H "APS-Token: JEFFUy0xMjgtR0NNJGZrLzJZdWp6aXlBbXZ1ZXEkVW1zZWV5V0J4d29yVzFMZklsNUt6S3ZqUFVSdzZnbyt1MEdzcWNMZmphSnJCZE02Mkt0eGp0VHZyU3YyNlZaZndBUk01elpwV004S0szaHlhWVl5amQ0SExJVVdSZFlGd2NFdzBLUGNPL2NPcHBOTThpdkd3OTQyZ2dSZURaYlJVam9CUkVzRkdMTE15dllNczZtb1ErZHhTcFVPcmFwSDMrcnRiR3pvUm1RYTlOczdTcE91VWdyQXEvcWhEUXlBMUk3WkVUZXJiU3phQnlCOEFTOEs5S2NocGlBaS8wRXFzbEZJNnJPOG51cVhncTJzblVUQkJiMDd0dStUSEtuVmpQaWE4TEtic1JMQ0dDcHY1K212M1FwQTFRVnNNU3ZXZzFjQkdCdktYRmJ6NHZidnhCY2tmTWRyN2cxVXp2SUpueSsyOC9SQ1VwNSs5SlpoSnBNQmdkQlBsb3NoUVpES3EwNm1uNmNtOXhTaUlYYmpkY0M1Qk0rRUxYU1h5VVRES1lIeVgvcHJmekNMZHc4bmlnUEQ3bVZrZDVnL21BM2NMeVFlSmtmV2JzZFVLWXNNVnp0eHU5ZHdHS1laZTF1RVcxSjM0dEhSN2VlZ0EvOElJZGY2NTZ3ZWhnWXdPREFMSmsxSElZejRvTHQ3RVI3VWpRbkVaMTVmMHVhNmNZVi9SVVlB"



curl http://poamn-0ef51a93a4d1.aqa.int.zone:8080/aps/2/resources?implementing(ttp://www.odin.com/platform-idp-support/1.1)


# Запуск spring boot в режиме Debug
mvn spring-boot:run -Dspring-boot.run.jvmArguments="-Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=y,address=5005"


mvn install -f modules/platform/cells/idp



## PUI WAR
# export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
# export PATH=${PATH}:${JAVA_HOME}/bin
export MN_HOST=POAMN-9f54412b7eaa.aqa.int.zone
export PCV=local
mvn install -f modules/platform/cells/idp && mvn install -f poa/pui/pui-shaded && mvn install -f poa/pui/pui-war && scp poa/pui/pui-war/target/pui-war.war root@$MN_HOST:/root && ssh root@$MN_HOST "time sh /usr/local/pem/wildfly-16.0.0.Final/bin/jboss-cli.sh --connect deploy\ -f\ /root/pui-war.war"




export IDP_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI3Z2pOVWd3NlNUNm1DanpuWE93TElkWGJDRE1SUmFsNXBfaG16Mzhob2tjIn0.eyJqdGkiOiI3OTk3YzM4Mi00NGZiLTRjMzYtYTIzMC0yZDIyOTNmMjM3ZTUiLCJleHAiOjE1ODM0MDk4NjAsIm5iZiI6MCwiaWF0IjoxNTgzNDA5NTYwLCJpc3MiOiJodHRwczovL21hYXNrLmJybmQxNTdmNzljZi0wNjRiNTMuYXFhLmludC56b25lL2F1dGgvcmVhbG1zL3NyMSIsImF1ZCI6ImNsaSIsInN1YiI6ImY6ZTgzMjRhODUtMzQxNC00MWM4LTgwMmItNTkyY2NjNmEwZTlkOjMiLCJ0eXAiOiJJRCIsImF6cCI6ImNsaSIsImF1dGhfdGltZSI6MCwic2Vzc2lvbl9zdGF0ZSI6ImY5M2FlNGYzLWEyMmEtNDg1NS1hNThiLTM3ZTNmY2I4MDEyYSIsImFjciI6IjEiLCJhY2NvdW50X2lkIjoxMDAwMDAxLCJ1c2VyX2lkIjo4LCJhY2NvdW50X3VpZCI6IjRkOTZhZmMyLTI2ZGQtNDcwNC04YWEwLTYyMmE4MmQyYzMxNyIsImFjY291bnRfaCI6IjEsMTAwMDAwMSJ9.HrQurRI-0cM9k0kRYaV4pu3ixOAVYMMmedlmrtGT08qFkYfashBfcKIfpmOUmtsPuOyv7Qd7RQ2ZTCKAj-699yS_XRWVTdIZtNCx_D67np3NpHAnjUJ5vs0o7JXwr5uhYFmPUrL7dSbVAYsRt18HdU-wCB6taaBuBD8dMEnY8d8sGkUqazyYDaKrx8L7JXJMryBNoSRdeYL_NXuTRwO1YF-ZBEEKTAiaD-JDIdCihIzoElW0e-IeowwhajHaeJAUntbQQsn76imiTkqUGb46ZkoLVVCkKd0BCy_-jpGyaZYZnFD0cFYAVIE1ZWwpm2gDhzUMs4DoA6Xi_SfRj8_oiQ
curl -k -v https://maask.brnd157f79cf-064b53.aqa.int.zone/aps/2/resources/ -H "Authorization: Bearer ${IDP_TOKEN}"



#Staff memmber password
1q2w3e!Q@W#E








mvnDebug install -e -B -DstackName=igor-platform-idp -Dspconfig.address=spconfig.int.zone -Dcucumber.options='classpath:features/qa/single_login_form2.feature' -Dcoverage=0 -DforkCount=0 -Dremote=http://localhost:4444/wd/hub



yum -y install ntp ntpdate
systemctl start ntpd
systemctl enable ntpd
ntpdate -u -s 0.centos.pool.ntp.org 1.centos.pool.ntp.org 2.centos.pool.ntp.org
date


export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export PATH=${PATH}:${JAVA_HOME}/bin



michael.rowe5695@POAMN-0ef51a93a4d1.aqa.int.zone



export MN_HOST=POAMN-a43636932874.aqa.int.zone
mvn clean install -f ./modules/platform/u/EAR/account-ejb && mvn clean install -f ./modules/platform/u/EAR/core-war && mvn clean install -f ./modules/platform/u/EAR/core-ear && scp ./modules/platform/u/EAR/core-ear/target/core-ear.ear root@$MN_HOST:/root/ && ssh root@$MN_HOST "sh /usr/local/pem/wildfly-16.0.0.Final/bin/jboss-cli.sh --connect -u=root -p=1  deploy\ -f\ /root/core-ear.ear"

export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export PATH=${PATH}:${JAVA_HOME}/bin
export MN_HOST=POAMN-0ef51a93a4d1.aqa.int.zone
export AUTO=925
mvn clean install -f ./modules/platform/u/EAR/core-war -Dauto=${AUTO}  && mvn clean install -f ./modules/platform/u/EAR/core-ear -Dauto=${AUTO}  && scp ./modules/platform/u/EAR/core-ear/target/core-ear.ear root@$MN_HOST:/root/ && ssh root@$MN_HOST "sh /usr/local/pem/wildfly-16.0.0.Final/bin/jboss-cli.sh --connect -u=root -p=1  deploy\ -f\ /root/core-ear.ear"


# Find with grep.
find . -not \( -path '*/target/*' -o -path '*/.git/*' \) -type f  -exec grep 'Fake Reseller' {} \; -print


docker run  -e DISPLAY=:1 -v /tmp/.X11-unix:/tmp/.X11-unix e80d8c416584



echo tGTQosyZ2019|sudo openconnect vpn.msk.odin.net --servercert sha256:ea6e7abba14fafa682a7a7e276b9a49f82c62baebe258d79db77bf2d40847996 --user=ibobko --authgroup=ODIN-Remote-Access --passwd-on-stdin -b







curl 'http://poamn-626bafe306c1.aqa.int.zone:8080/aps/2/resources/0cadf371-7004-4223-a1bb-b67fe2372670/bss/account/currency-states' \
  -H 'APS-Token: JEFFUy0xMjgtR0NNJENMRk16UWJGT2xyVWZuMUUkUG02Qko1MnV1V2VSNWJBTWJuWEFOY2JCdXBFZ1lodVN3Z1FDekh5Q3JGRTNwRm5lb1dHVDRZYVl2dFJKdUZDOVRGOENJbmZwaVBsUnBUbVZlOFpEVE1LbFBqR3V1VzEvOUxPRG5LWXIwU1F3ZWdGQWxoQ3dIc1NCQ2ExeHB4Tk56NWV6c1g5ZGw5UFpvUHRib0QyMzF0WmUydEpnd0ZaY1ZPZS83em9zT3hTSXljZ1YwRHFPVVBtUCt2UnRwVU1lYXF3ajl5bmFLL0E0czNXNmQxMUcraVp5TGNrVUFlM2lPeTVZbU0xTVZOdVRodVBiT3JrOFFWUGV1ZXpOeWtpM2ZGVDhCcFBGT2IzMFpTdXg5SDRvM0U0TXQyS1JvRnRqMXhiTDVoR3QxQU03VXJSZTdpc290N0ZZU04vQjQvRVZkckFjZG9JSXhsbXI5WWt4eFNBK0krTTZyQTZpOFdIdzVSOEZ5Y0VKbjQxZDBvQy9zang4aUwyNTBxY0RqQ2NtUi9ReVNKbkhabnpxUXRSSHNnVUJWT1dQMTUwdXJHSDdHdm1ZN3lMZVo0bUxhU3laaHJXVlNxa0t4ZnhnVS9BZWdNVjBlbjBuYWtxdmJwOEV6TlBPMmFWVlVOekdiN1dXNnNQZ28wa1FpeldsNGJ5Y2xnRm1hSzF5eFUzZGRvMzlyZkExR0QydHJXYzU3ZStmZU5YRDgwWThQeTJaeHRJbllvb3hLM2lz' \
  -H 'APS-Actor-Scope: VENDOR_PUBLIC'