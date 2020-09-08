from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import driver


class SPConfig:
    def __init__(self):
        self.driver = driver.get_driver()

    def auth_spconfig(self):
        self.driver.get("http://spconfig.int.zone/")
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "id_username")))
        self.driver.find_element_by_id("id_username").send_keys("platform-tools")
        self.driver.find_element_by_id("id_password").send_keys("1q2w3e")
        self.driver.find_element_by_css_selector('[type = "submit"]').click()

    def create_idp_stack(self, cb_version):
        self.driver.get("http://spconfig.int.zone/")
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "btn-create")))
        self.driver.find_element_by_class_name("btn-create").click()
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "id_http_url")))
        self.driver.find_element_by_id("id_http_url")
        template = self.driver.find_element_by_id('id_http_url')
        for option in template.find_elements_by_tag_name('option'):
            if option.get_attribute(
                    "value") == 'http://spconfig.int.zone:8080/templates/parallels/platform_with_idp.template.json':
                option.click()  # select() in earlier versions of webdriver
                break

        self.driver.find_element_by_css_selector('input.pull-right').click()
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "id_stack_name")))

        from random import randint

        stack_name = "igor-idp-{}".format(randint(1, 99))

        self.driver.execute_script("arguments[0].value = '{}';".format(stack_name),
                                   self.driver.find_element_by_id("id_stack_name"))
        node = self.driver.find_element_by_id('id_HWNode')
        for option in node.find_elements_by_tag_name('option'):
            if option.text == "honey.int.zone":
                option.click()
                break

        self.driver.find_element_by_id("id_Build").send_keys(cb_version)
        self.driver.find_element_by_css_selector('[type = "submit"]').click()
        return stack_name

    def get_version_form_spboard(self):
        import re
        self.driver.get("http://spboard.int.zone/PA/")
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".content")))
        tables = self.driver.find_elements_by_css_selector(".content .status-table")
        for table in tables:
            cols = table.find_elements_by_tag_name("td")
            info = cols[1].find_element_by_class_name("info")
            version = info.get_attribute("innerText").strip()
            return re.search(r"\((\S+)\)", version).group(1)
