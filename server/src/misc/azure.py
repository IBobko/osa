data = [
  {
    "name": "APP_NAME",
    "value": "bi-irs-imc",
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
    "value": "bidatalakeimc.azuredatalakestore.net",
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
    "value": "https://prod-56.westeurope.logic.azure.com:443/workflows/359030c61e7d4b6199cb6bbf47f79ce7/triggers/manual/paths/invoke?api-version=2016-10-01&sp=/triggers/manual/run&sv=1.0&sig=bjUxgut05KdY2bcVnUXmoWaO9a2UmXtVyQa7Fpyne1w",
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
    "value": "bi-sql-imc.database.windows.net",
    "slotSetting": False
  },
  {
    "name": "SQL_PASSWORD",
    "value": "1q@w3e4r5t6Y",
    "slotSetting": False
  },
  {
    "name": "SQL_USER",
    "value": "bi-user",
    "slotSetting": False
  },
  {
    "name": "STAGE",
    "value": "master-dev",
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
  },
  {
    "name": "WEBSITE_HTTPLOGGING_RETENTION_DAYS",
    "value": "3",
    "slotSetting": False
  }
]

if __name__ == '__main__':
    for row in data:
        print("export {}=\"{}\"".format(row['name'],row['value']))