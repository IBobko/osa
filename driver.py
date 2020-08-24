from selenium import webdriver

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('ignore-certificate-errors')
driver = webdriver.Opera(options=chrome_options, executable_path='./operadriver')
