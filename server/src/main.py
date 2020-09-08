import uuid

import paramiko
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from server.src import aps, billing_

from server.src.driver import driver

brand_domain = "nmwUG.brnd17498abd-c1af32.aqa.int.zone"
mn_domain = "POAMN-fd77f32e3ab1.aqa.int.zone"

register_data = {
    "username": "alfred3",
    "password": "tGTQosyZ2010@!"
}


def create_user_on_mn(host, username):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username="root", password="1q2w3e")
    client.exec_command('adduser {}'.format(username))
    client.close()


def get_email_code(host, username):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username="root", password="1q2w3e")
    stdin, stdout, stderr = client.exec_command('cat /var/spool/mail/{}'.format(username))
    mails = stdout.readlines()
    mails.reverse()
    client.close()
    return mails[7].strip()


def register(signup_url, mn, data):
    import time
    time.sleep(2)
    create_user_on_mn(mn, data['username'])

    driver.get(signup_url)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'email')))
    driver.find_element_by_id("email").send_keys("{}@{}".format(data['username'], mn))
    driver.find_element_by_id("password").send_keys(data['password'])
    driver.find_element_by_id("login").click()
    code = get_email_code(mn, data['username'])
    driver.find_element_by_id("email_verify_code").send_keys(code)
    driver.find_element_by_id("login").click()

    time.sleep(4)
    driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])

    driver.find_element_by_id("onboarding-anonymous-singup-complete_companyName").send_keys('Company Name')
    driver.find_element_by_id("onboarding-anonymous-singup-complete_adminFirstName").send_keys('John')
    driver.find_element_by_id("onboarding-anonymous-singup-complete_adminLastName").send_keys('Smith')
    driver.find_element_by_id("onboarding-anonymous-singup-complete_streetAddress").send_keys('Glen Park Avenue')
    driver.find_element_by_id("onboarding-anonymous-singup-complete_locality").send_keys("Plymouth")

    driver.find_element_by_id("onboarding-anonymous-singup-complete_zip").send_keys('02360')
    country = driver.find_element_by_id("onboarding-anonymous-singup-complete_country")
    country.send_keys('United Kingdom')
    WebDriverWait(driver, 10) \
        .until(EC.element_to_be_clickable((By.ID, 'onboarding-anonymous-singup-complete_country_popup')))
    driver.find_element_by_id("onboarding-anonymous-singup-complete_country_popup").find_element_by_tag_name(
        "a").click()
    driver.find_element_by_id("onboarding-anonymous-singup-complete_region").send_keys("Devon")

    driver.find_element_by_id("onboarding-anonymous-singup-complete_adminPhone").send_keys('+4401752942971')
    driver.find_element_by_id("onboarding-anonymous-singup-complete_createAccount").click()


def authentication(url, login, password):
    driver.get("https://{}".format(url))
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'inp_user')))
    driver.find_element_by_id("inp_user").send_keys(login)
    driver.find_element_by_id("inp_password").send_keys(password)
    driver.find_element_by_id("login").click()


def authentication_mn(url, login, password):
    driver.get("http://{}:8080".format(url))
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'inp_user')))
    driver.find_element_by_id("inp_user").send_keys(login)
    driver.find_element_by_id("inp_password").send_keys(password)
    driver.find_element_by_id("login").click()


def onboarding_enabling():
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'http://cloudblue.com/uam#onboarding')))
    driver.find_element_by_id('http://cloudblue.com/uam#onboarding').click()

    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it('http://cloudblue.com/uam'))
    driver.find_element_by_id("onboarding-configuration_start").click()

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'onboarding-configuration_accessLink')))

    value = driver.find_element_by_id("onboarding-configuration_accessLink").get_attribute("value")
    uid = str(uuid.uuid1())
    driver.find_element_by_id("onboarding-configuration_accessLink").send_keys(uid)
    driver.find_element_by_id("onboarding-configuration_enableCustomersSignUp").find_element_by_tag_name(
        "button").click()
    driver.find_element_by_id("onboarding-configuration_save").click()
    WebDriverWait(driver, 10) \
        .until(EC.element_to_be_clickable((By.ID, 'onboarding-configuration_entryPointUrl')))

    return "{}{}".format(value, uid)


if __name__ == '__main__':
    credentials = aps.create_account_with_user(brand_domain)
    authentication_mn(mn_domain, "admin", "1q2w3e")
    billing_.billing(credentials['id'])

    suffix = onboarding_enabling()
    reg_data = register_data.copy()

    import random
    import string

    reg_data['username'] = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(12)]).lower()
    register("https://{}{}".format(brand_domain, suffix), mn_domain, reg_data)
    import time

    time.sleep(5)
    reg_data['username'] = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(12)]).lower()
    register("https://{}{}".format(brand_domain, suffix), mn_domain, reg_data)
