from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
from pymongo import UpdateOne

DISCORD_EMAIL = os.environ.get('DISCORD_EMAIL')
DISCORD_PASSWORD = os.environ.get('DISCORD_PASSWORD')


def join_discord(discord_email, discord_password, db):
    # Use the `install()` method to set `executabe_path` in a new `Service` instance:
    service = Service(executable_path=ChromeDriverManager().install())

    # Pass in the `Service` instance with the `service` keyword:
    driver = webdriver.Chrome(service=service)

    discord_links = db.discord_link.find({"joined": False})
    updates = []
    errors = []

    for link in discord_links:
        try:
            driver.get(link['url'])
            driver.set_window_size(1440, 816)
            element_exists_number = len(driver.find_elements(
                By.CSS_SELECTOR, ".marginTop8-24uXGp > .contents-3ca1mk"))

            # Check if the "have an account already" button exists. If it does, then log in with our credentials
            if driver.execute_script("return (arguments[0] == 1)", element_exists_number):
                driver.find_element(
                    By.CSS_SELECTOR, ".marginTop8-24uXGp > .contents-3ca1mk").click()
                driver.find_element(
                    By.NAME, "email").send_keys(discord_email)
                driver.find_element(By.CSS_SELECTOR, ".wrapper-1f5byN").click()
                driver.find_element(By.NAME, "password").click()
                driver.find_element(By.NAME, "password").send_keys(
                    discord_password)
                driver.find_element(By.CSS_SELECTOR, ".button-1cRKG6").click()
            else:
                driver.find_element(
                    By.CSS_SELECTOR, ".marginTop40-Q4o1tS").click()

            updates.append(UpdateOne({'_id': link['_id']},
                                     {'$set': {
                                         'joined': True
                                     }},
                                     ))
        except:
            errors.append(link)
        time.sleep(7)

    driver.close()

    joined_urls = db.discord_link
    joined_results = joined_urls.bulk_write(updates)
    print(
        f"Joined {joined_results.modified_count} Discord servers!")
    print(
        f"There were errors in joining {len(errors)} servers.")

    # driver.execute_script("window.scrollTo(0,0)")
    # element = driver.find_element(By.CSS_SELECTOR, ".anchor-1MIwyf")
    # actions = ActionChains(driver)
    # actions.move_to_element(element).perform()
    # element = driver.find_element(
    #     By.CSS_SELECTOR, ".containerDefault-YUSmu3:nth-child(6) .channelName-3KPsGw")
    # actions = ActionChains(driver)
    # actions.move_to_element(element).perform()
    # driver.find_element(
    #     By.CSS_SELECTOR, ".containerDefault-YUSmu3:nth-child(6) .channelName-3KPsGw").click()
    # driver.execute_script("window.scrollTo(0,0)")
    # element = driver.find_element(By.LINK_TEXT, "✅｜verify")
    # actions = ActionChains(driver)
    # actions.move_to_element(element).perform()
    # driver.find_element(
    #     By.CSS_SELECTOR, "div:nth-child(1) > .reaction-2A2y9y .reactionCount-1zkLcN").click()
