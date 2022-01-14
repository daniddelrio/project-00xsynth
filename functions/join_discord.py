from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from pymongo import UpdateOne
import traceback


def join_discord(discord_email, discord_password, db):
    # Use the `install()` method to set `executabe_path` in a new `Service` instance:
    service = Service(executable_path=ChromeDriverManager().install())

    # Pass in the `Service` instance with the `service` keyword:
    driver = webdriver.Chrome(service=service)

    discord_links = db.discord_link.find({"joined": False})
    updates = []
    errors_joining = []
    success_verifying = []

    for link in discord_links:
        able_to_join = True
        update_obj = None
        try:
            driver.get(link['url'])
            time.sleep(3)
            element_exists_number = len(driver.find_elements(By.XPATH,
                                                             "//*[contains(text(),'Already have an account')]"))

            # Check if the "have an account already" button exists. If it does, then log in with our credentials
            if driver.execute_script("return (arguments[0] == 1)", element_exists_number):
                driver.find_element(
                    By.XPATH, "//*[contains(text(),'Already have an account')]").find_element(By.XPATH, "./..").click()
                driver.find_element(
                    By.NAME, "email").send_keys(discord_email)
                driver.find_element(By.CSS_SELECTOR, ".wrapper-1f5byN").click()
                driver.find_element(By.NAME, "password").click()
                driver.find_element(By.NAME, "password").send_keys(
                    discord_password)
                driver.find_element(By.CSS_SELECTOR, ".button-1cRKG6").click()
            else:
                found_accept_invite = len(driver.find_elements(
                    By.XPATH, "//div[text()='Accept Invite']"))
                cap_while_loop = 0
                while found_accept_invite == 0:
                    found_accept_invite = len(driver.find_elements(
                        By.XPATH, "//div[text()='Accept Invite']"))
                    time.sleep(2)
                    cap_while_loop += 2

                    if cap_while_loop >= 10:
                        break

                driver.find_element(
                    By.XPATH, "//div[text()='Accept Invite']").find_element(By.XPATH, "./..").click()

            update_obj = UpdateOne({'_id': link['_id']},
                                   {'$set': {
                                       'joined': True
                                   }},
                                   )

        except Exception as e:
            print(traceback.format_exc())
            errors_joining.append(link)
            able_to_join = False

        if able_to_join:
            try:
                time.sleep(3)

                # Clicking "Continue" for page on "Discord App Launched"
                has_discord_app_launched = len(driver.find_elements(By.XPATH,
                                                                    "//*[contains(text(),'Discord App Launched')]"))
                if driver.execute_script("return (arguments[0] == 1)", has_discord_app_launched):
                    driver.find_element(
                        By.XPATH, "//*[contains(text(),'Continue to Discord')]").find_element(By.XPATH, "./..").click()
                    time.sleep(3)

                time.sleep(5)
                # Finding the channel that contains the word "verif" for "verify" or "verifications" or "rules"
                found_channel = False
                for channel in driver.find_elements(By.CSS_SELECTOR, ".mainContent-20q_Hp"):
                    channel_name = channel.find_element(
                        By.CSS_SELECTOR, ".channelName-3KPsGw").text
                    if 'verif' in channel_name:
                        channel.click()
                        found_channel = True
                        break

                if not found_channel:
                    raise Exception("Was not able to find the verify channel")

                # Verifying by clicking the first five reactions on the message
                time.sleep(3)
                for count, reaction in enumerate(driver.find_elements(By.CLASS_NAME, "reaction-2A2y9y")):
                    if count >= 5:
                        break

                    reaction.find_element(
                        By.CLASS_NAME, "reactionInner-9eVHJa").click()
                    time.sleep(1.5)

                    # Just in case we need to agree to the rules and submit
                    has_agree = len(driver.find_elements(By.CSS_SELECTOR,
                                                         ".checkboxText-2F08go"))
                    if has_agree > 0:
                        driver.find_element(By.CSS_SELECTOR,
                                            ".checkboxText-2F08go").click()
                        driver.find_element(By.CSS_SELECTOR,
                                            ".submitButton-34IPxt").click()
                        time.sleep(1.5)

                success_verifying.append(link)
                update_obj = UpdateOne({'_id': link['_id']},
                                       {'$set': {
                                           'joined': True,
                                           'verified': True
                                       }},
                                       )

                # If necessary, go through steps to be able to talk by agreeing to the rules
                has_submit_rules = len(driver.find_elements(By.CSS_SELECTOR,
                                                            ".button-cO0-d9 > .contents-3ca1mk"))
                if driver.execute_script("return (arguments[0] == 1)", has_submit_rules):
                    driver.find_element(By.CSS_SELECTOR,
                                        ".button-cO0-d9 > .contents-3ca1mk").click()
                    driver.find_element(By.CSS_SELECTOR,
                                        ".checkboxText-2F08go").click()
                    driver.find_element(By.CSS_SELECTOR,
                                        ".submitButton-34IPxt").click()

            except Exception as e:
                print(traceback.format_exc())

        if update_obj:
            updates.append(update_obj)
        time.sleep(60)

    driver.close()

    joined_urls = db.discord_link
    joined_results = joined_urls.bulk_write(updates)
    print(
        f"Joined {joined_results.modified_count} Discord servers!")
    print(
        f"There were errors in joining {len(errors_joining)} servers.")
    print(
        f"Out of {joined_results.modified_count} servers, we were able to verify in {len(success_verifying)}")
