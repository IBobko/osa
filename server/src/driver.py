from selenium import webdriver


def get_driver():
    capabilities = webdriver.DesiredCapabilities.OPERA.copy()
    capabilities['acceptSslCerts'] = True

    return webdriver.Remote(desired_capabilities=capabilities,
                            command_executor='http://selenium:4444/wd/hub')


driver = get_driver()
