from selenium import webdriver

capabilities = webdriver.DesiredCapabilities.OPERA.copy()
capabilities['acceptSslCerts'] = True

driver = webdriver.Remote(desired_capabilities=capabilities,
                        command_executor='http://selenium:4444/wd/hub')


def get_driver():
    global driver
    return driver
