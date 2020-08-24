from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from driver import driver


def billing(account_id):
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it('topFrame'))
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'to_bm')))
    driver.find_element_by_id("to_bm").click()
    driver.switch_to.default_content()
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it('leftFrame'))
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'click_subscriptions')))
    driver.find_element_by_id("click_subscriptions").click()
    driver.switch_to.default_content()
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it('mainFrame'))
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'input___add')))

    driver.find_element_by_id("input___add").click()

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'input___AccountAccountID')))
    driver.find_element_by_id("input___AccountAccountID").send_keys(account_id)
    driver.find_element_by_id("input___PlanPlanID").send_keys("4")
    driver.find_element_by_id("input___refPlanPeriod").click()

    win_handle_before = driver.current_window_handle

    driver.switch_to.window("popup2")
    driver.find_element_by_id("screenID")

    driver.find_element_by_id("global_list") \
        .find_element_by_tag_name("tbody") \
        .find_element_by_class_name("group-member").click()

    driver.switch_to.window(win_handle_before)
    driver.switch_to.frame("mainFrame")
    driver.find_element_by_id("input___SaveAdd").click()
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'input____DomainID')))
    driver.find_element_by_id("input____DomainID").send_keys("agCDY.brnd17498abd-c1af32.aqa.int.zone")
    driver.find_element_by_id("input___Next").click()

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'input___PayToolPayToolID')))
    driver.execute_script("arguments[0].value = '0';", driver.find_element_by_id("input___PayToolPayToolID"))
    driver.find_element_by_id("input___SP_ViewPromoOrder").click()

    if driver.find_element_by_id("_browse_search").is_displayed():
        driver.execute_script(f"arguments[0].value = '{account_id}';",
                              driver.find_element_by_id("filter_AccountID"))
        driver.find_element_by_id("_browse_search").click()

    driver.implicitly_wait(2)

    rows = driver.find_element_by_id("global_list") \
        .find_element_by_tag_name("tbody").find_elements_by_tag_name("tr")

    for row in rows:
        cols = row.find_elements_by_tag_name("td")
        if cols[9].get_attribute("innerText") == str(account_id):
            cols[0].find_element_by_tag_name("a").click()

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'webgate__tab_3')))
    driver.find_element_by_id("webgate__tab_3").click()

    driver.find_element_by_id("global_list") \
        .find_element_by_tag_name("tbody").find_element_by_tag_name("tr").find_element_by_tag_name("a").click()
    driver.find_element_by_id("input___OF_OP").click()

    import time

    time.sleep(2)
    driver.find_element_by_id("webgate__tab_4").click()

    time.sleep(2)
    driver.find_element_by_id("global_list") \
        .find_element_by_tag_name("tbody").find_element_by_tag_name("tr").find_element_by_tag_name("a").click()

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'input___Release')))
    driver.find_element_by_id("input___Release").click()

    time.sleep(2)
    driver.switch_to.default_content()
    WebDriverWait(driver, 20).until(EC.frame_to_be_available_and_switch_to_it('leftFrame'))
    driver.find_element_by_id("click_my_reseller_accounts").click()

    time.sleep(2)

    driver.switch_to.default_content()
    driver.switch_to.frame("mainFrame")
    pass

    if driver.find_element_by_id("_browse_search").is_displayed():
        driver.find_element_by_id("_browse_reset_search").click()

        driver.execute_script(f"arguments[0].value = '{account_id}';",
                              driver.find_element_by_id("filter_AccountID"))
        driver.find_element_by_id("_browse_search").click()
        driver.find_element_by_id("click_my_reseller_accounts").click()

    time.sleep(2)

    rows = driver.find_element_by_id("global_list") \
        .find_element_by_tag_name("tbody").find_elements_by_tag_name("tr")

    for row in rows:
        cols = row.find_elements_by_tag_name("td")
        if cols[1].get_attribute("innerText") == str(account_id):
            cols[11].find_element_by_tag_name("a").click()

    time.sleep(2)

    window_before = driver.window_handles[0]
    window_after = driver.window_handles[1]
    driver.switch_to.window(window_after)

    driver.find_element_by_id("input___Save").click()
