import json
import logging
import uuid

from requests_oauthlib import OAuth1Session

logging.basicConfig(level=logging.INFO)

consumer_key = 'wS99vaLNiWJr60S7eK7vJNBtRzXfW8rX'
consumer_secret = 'Kh8CICUzsLA6SeTWY108vGDPB88JOUjgu3zavZ1kt5oP1R8glOmeO4AgK5nvtqeTykcZz6EUYCnZMwmIdZIFW6Mr5TsMHiZtQuQZsBGc7A8565graQvngmVdRQoynUXt'


def f(brand_domain):
    uid = uuid.uuid1()
    url = 'https://{}/aps/2/resources'.format(brand_domain)
    session = OAuth1Session(consumer_key, consumer_secret)
    subscription = {
        "name": "Auto_Reseller Branding for POA + PBA7322033",
        "trial": False,
        "disabled": False,
        "description": "",
        "isTerminated": False,
        "subscriptionId": 1000037,
        "serviceTemplateId": 12,
        "aps": {
            "id": str(uid),
            "type": "http://parallels.com/aps/types/pa/subscription/1.0"
        }
    }
    response = session.post(url, json=subscription, verify=False)
    print(response.text)


def subscriptions(brand_domain):
    url = 'https://{}/aps/2/collections/subscriptions'.format(brand_domain)
    session = OAuth1Session(consumer_key, consumer_secret)
    response = session.get(url, verify=False)
    print(response.text)


def create_account_with_user(brand_domain):
    url = 'https://{}/aps/2/resources'.format(brand_domain)

    session = OAuth1Session(consumer_key, consumer_secret)

    uid = uuid.uuid1()
    accounts = [
        {
            "aps": {
                "type": "http://parallels.com/pa/bss-account-info/1.0",
                "id": str(uid)
            },
            "taxStatus": "PROVIDER",
            "localeId": "en_US",
            "taxRegId": "1111",
            "status": "CREDIT_HOLD"

        },
        {
            "aps": {
                "type": "http://parallels.com/aps/types/pa/account/1.2"
            },
            "type": "RESELLER",
            "personal": False,
            "companyName": "1st APS inc",
            "bssAccountInfo": {
                "aps": {
                    "id": str(uid)
                }
            },
            # "parent":{
            #    "aps":{
            #       "id":"4935d68d-4d26-4930-acf7-3871557305a9"
            #    }
            # },
            "addressPostal": {
                "countryName": "us",
                "locality": "APS",
                "postalCode": "12345",
                "region": "VA",
                "streetAddress": "11, APS"
            },
            "adminContact": {
                "email": "isv1@aps.test",
                "givenName": "Mike",
                "familyName": "Wilson",
                "telVoice": "1#888#1234567"
            },
            "billingContact": {
                "email": "isv1@aps.test",
                "givenName": "Mike",
                "familyName": "Wilson",
                "telVoice": "1#888#1234567"
            },
            "techContact": {
                "email": "isv1@aps.test",
                "givenName": "Mike",
                "familyName": "Wilson",
                "telVoice": "1#888#1234567"
            }
        },
        {
            "aps": {
                "type": "http://parallels.com/aps/types/pa/admin-user/1.2"
            },
            "isAccountAdmin": True,
            "login": "mw@aps.test" + str(uid),
            "password": "p@$$w0rd",
            "email": "mw@aps.test",
            "givenName": "Mike",
            "familyName": "Wilson",
            "telVoice": "1(888)1234567",
            "addressPostal": {
                "streetAddress": "11, ISVone",
                "locality": "Herndon",
                "region": "VA",
                "countryName": "us",
                "postalCode": "12345"
            }
        }
    ]
    response = session.post(url, json=accounts, verify=False)
    json_response = json.loads(response.text)
    logging.info(json_response)
    return {
        "username": "mw@aps.test" + str(uid),
        "password": "p@$$w0rd",
        "id": json_response[0]['accountId']
    }


if __name__ == '__main__':
    create_account_with_user("nmwUG.brnd17498abd-c1af32.aqa.int.zone")
    # subscriptions("agCDY.brnd17498abd-c1af32.aqa.int.zone")
    # create_account_with_user("agCDY.brnd17498abd-c1af32.aqa.int.zone")
