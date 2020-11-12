import json

data = [
  {
    "name": "APP_NAME",
    "value": "imc-dev-736-mwe1-globus-irs-appservice",
    "slotSetting": False
  },
  {
    "name": "APPLICATION_INSIGHTS_IKEY",
    "value": "956b49bf-d03b-4db3-bee1-0c2379ad5516",
    "slotSetting": False
  },
  {
    "name": "CLIENT_ID_AD",
    "value": "ad2090c0-79bb-4c13-a666-0dc6d723e09b",
    "slotSetting": False
  },
  {
    "name": "CLIENT_ID_DATALAKE",
    "value": "15662ad2-b6eb-4776-a788-9c7e0aaa8ce5",
    "slotSetting": False
  },
  {
    "name": "CLIENT_SECRET_AD",
    "value": "JS9W2v5m4ZfxQb613fm91oueuJSTaSfapEmrEXJUykE=",
    "slotSetting": False
  },
  {
    "name": "CLIENT_SECRET_DATALAKE",
    "value": "ZmkpgSa4WQXciH63bYmev4kMdZ7pr0ol4pR5da5FyJM=",
    "slotSetting": False
  },
  {
    "name": "DATALAKE_HOST",
    "value": "imcdev736mwe1globusdls.azuredatalakestore.net",
    "slotSetting": False
  },
  {
    "name": "JAVA_OPTS",
    "value": "-Dserver.port=80 -Xms2048m -Xmx6144m -Dorg.wildfly.openssl.path=/tmp",
    "slotSetting": False
  },
  {
    "name": "MAIL_PASSWORD",
    "value": "",
    "slotSetting": False
  },
  {
    "name": "MAIL_USERNAME",
    "value": "Svc-cloud-platform-cep@ingrammicro.com",
    "slotSetting": False
  },
  {
    "name": "RUMS_MONITOR_URL",
    "value": "",
    "slotSetting": False
  },
  {
    "name": "SALESFORCE_CLIENT_ID",
    "value": "3MVG99OxTyEMCQ3gIn7i.gkm.FeUIGPYzKVGnbtn1p_pi8dLxmh7Fe38XbQVaSeih4xCH9IVfjuWrNS1RPK4L",
    "slotSetting": False
  },
  {
    "name": "SALESFORCE_CLIENT_SECRET",
    "value": "1154D72AFF146CF6CD6A07E5D5AB9380EF30E32CA68DA40AFEB7CDBFA05EC1B6__",
    "slotSetting": False
  },
  {
    "name": "SALESFORCE_LOGIN_URL",
    "value": "https://login.salesforce.com/services/oauth2/token",
    "slotSetting": False
  },
  {
    "name": "SALESFORCE_PASSWORD",
    "value": "Y<ZPvMsYMfdA8nZP__",
    "slotSetting": False
  },
  {
    "name": "SALESFORCE_REST_URL",
    "value": "https://cloudblue.my.salesforce.com/services/data/v37.0",
    "slotSetting": False
  },
  {
    "name": "SALESFORCE_SECURITY_TOKEN",
    "value": "1tOo7SzdNT9UKGIHwgGKBRbJ__",
    "slotSetting": False
  },
  {
    "name": "SALESFORCE_USER_NAME",
    "value": "cloud-a-team@ingrammicro.com",
    "slotSetting": False
  },
  {
    "name": "SQL_DB",
    "value": "irs",
    "slotSetting": False
  },
  {
    "name": "SQL_HOST",
    "value": "imc-dev-736-mwe1-astrum-azuresql.database.windows.net",
    "slotSetting": False
  },
  {
    "name": "SQL_PASSWORD",
    "value": "_ce1718518b0612a2f522afdeeb6641ea091973d4a712c1c7",
    "slotSetting": False
  },
  {
    "name": "SQL_USER",
    "value": "bi-user",
    "slotSetting": False
  },
  {
    "name": "STAGE",
    "value": "dev",
    "slotSetting": False
  },
  {
    "name": "TENANT_AD",
    "value": "b44641f9-e36e-4d7f-a3c4-eb3b991b6120",
    "slotSetting": False
  },
  {
    "name": "TENANT_DATALAKE",
    "value": "b44641f9-e36e-4d7f-a3c4-eb3b991b6120",
    "slotSetting": False
  }
]


def export_for_bash():
    for row in data:
        print("export {}=\"{}\"".format(row['name'], row['value']))


def export_for_docker():
    for row in data:
        if row['name'] in ('SQL_HOST','SQL_DB','SQL_USER','SQL_PASSWORD','CLIENT_ID_DATALAKE',
                           'CLIENT_SECRET_DATALAKE','TENANT_DATALAKE','DATALAKE_HOST'):
            print("ENV {}=\"{}\"".format(row['name'], row['value']))


def export_to_azure():
    result = []
    for row in data:
        if row['name'] in ('SQL_HOST','SQL_DB','SQL_USER','SQL_PASSWORD','CLIENT_ID_DATALAKE',
                           'CLIENT_SECRET_DATALAKE','TENANT_DATALAKE','DATALAKE_HOST'):
            result.append(row)
    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    export_for_bash()
    print("--------------------------------")
    export_for_docker()
    print("--------------------------------")
    export_to_azure()
