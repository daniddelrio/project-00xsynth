from pymongo import MongoClient
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from pymongo import UpdateOne
import traceback
import os
from utils.custom_logger import setup_logger
from utils.mongo_client import db

logger = setup_logger("join_discord")


class InvalidLinkException(Exception):
    pass


class NoVerifyChannelException(Exception):
    pass


def handler(event, context):
    DISCORD_EMAIL = os.environ.get("DISCORD_EMAIL")
    DISCORD_PASSWORD = os.environ.get("DISCORD_PASSWORD")

    limit = event.get("Limit", 10)

    # Use the `install()` method to set `executabe_path` in a new `Service` instance:
    service = Service(executable_path=ChromeDriverManager().install())

    options = Options()
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-gpu')
    options.headless = True

    # Pass in the `Service` instance with the `service` keyword:
    driver = webdriver.Chrome(service=service, options=options)

    # Limiting the automation to a few entries at a time
    discord_links = db.discord_link.find({"joined": False, "valid": True}).limit(limit)
    updates = []
    invalid_links = []
    new_watchlist = []
    old_approved = []
    errors_joining = []
    success_verifying = []

    for link in discord_links:
        able_to_join = True
        update_obj = None
        url = link["url"]
        id = link["_id"]
        try:
            driver.get(link["url"])
            time.sleep(3)
            invite_invalid_number = len(
                driver.find_elements(By.XPATH, "//*[contains(text(),'Invite Invalid')]")
            )

            if invite_invalid_number > 0:
                raise InvalidLinkException("Invite link is invalid!")

            element_exists_number = len(
                driver.find_elements(
                    By.XPATH, "//*[contains(text(),'Already have an account')]"
                )
            )

            # Check if the "have an account already" button exists. If it does, then log in with our credentials
            if driver.execute_script(
                "return (arguments[0] == 1)", element_exists_number
            ):
                driver.find_element(
                    By.XPATH, "//*[contains(text(),'Already have an account')]"
                ).find_element(By.XPATH, "./..").click()
                driver.find_element(By.NAME, "email").send_keys(DISCORD_EMAIL)
                driver.find_element(By.CSS_SELECTOR, ".wrapper-1f5byN").click()
                driver.find_element(By.NAME, "password").click()
                driver.find_element(By.NAME, "password").send_keys(DISCORD_PASSWORD)
                driver.find_element(By.CSS_SELECTOR, ".button-1cRKG6").click()
            else:
                found_accept_invite = len(
                    driver.find_elements(By.XPATH, "//div[text()='Accept Invite']")
                )
                cap_while_loop = 0
                while found_accept_invite == 0:
                    found_accept_invite = len(
                        driver.find_elements(By.XPATH, "//div[text()='Accept Invite']")
                    )
                    time.sleep(2)
                    cap_while_loop += 2

                    if cap_while_loop >= 10:
                        break

                driver.find_element(
                    By.XPATH, "//div[text()='Accept Invite']"
                ).find_element(By.XPATH, "./..").click()

            logger.info(f"Joined invite from {url} (id {id})")
            update_obj = UpdateOne(
                {"_id": link["_id"]},
                {"$set": {"joined": True}},
            )
        except InvalidLinkException as e:
            logger.warning(f"Invalid invite from {url} (id {id})")
            # print(traceback.format_exc())
            invalid_links.append(
                UpdateOne(
                    {"_id": link["_id"]},
                    {"$set": {"valid": False}},
                )
            )
            timestamp = datetime.datetime.utcnow()

            old_approved.append(link["account_id"])
            new_watchlist.append(
                UpdateOne(
                    {"account_id": link["account_id"]},
                    {
                        "$setOnInsert": {
                            "account_id": link["account_id"],
                            "timestamp": timestamp,
                        }
                    },
                    upsert=True,
                )
            )

            continue
        except Exception as e:
            logger.error(f"Error in trying to join {url} (id {id})")
            # print(traceback.format_exc())
            errors_joining.append(link)
            able_to_join = False

        if able_to_join:
            try:
                time.sleep(3)

                # Clicking "Continue" for page on "Discord App Launched"
                has_discord_app_launched = len(
                    driver.find_elements(
                        By.XPATH, "//*[contains(text(),'Discord App Launched')]"
                    )
                )
                if driver.execute_script(
                    "return (arguments[0] == 1)", has_discord_app_launched
                ):
                    driver.find_element(
                        By.XPATH, "//*[contains(text(),'Continue to Discord')]"
                    ).find_element(By.XPATH, "./..").click()
                    time.sleep(3)

                time.sleep(7)
                # Finding the channel that contains the word "verif" for "verify" or "verifications" or "rules"
                found_channel = False
                for channel in driver.find_elements(
                    By.CSS_SELECTOR, ".mainContent-20q_Hp"
                ):
                    channel_name = channel.find_element(
                        By.CSS_SELECTOR, ".channelName-3KPsGw"
                    ).text
                    if "verif" in channel_name:
                        logger.info(f"Found channel {channel_name} in {url} (id {id})")
                        channel.click()
                        found_channel = True
                        break

                if not found_channel:
                    raise NoVerifyChannelException(
                        "Was not able to find the verify channel"
                    )

                # Verifying by clicking the first five reactions on the message
                time.sleep(4)
                for count, reaction in enumerate(
                    driver.find_elements(By.CLASS_NAME, "reaction-2A2y9y")
                ):
                    if count >= 5:
                        break

                    logger.info(f"Reacting #{count+1} in {url} (id {id})")
                    reaction.find_element(By.CLASS_NAME, "reactionInner-9eVHJa").click()
                    time.sleep(1.5)

                    # Just in case we need to agree to the rules and submit
                    has_agree = len(
                        driver.find_elements(By.CSS_SELECTOR, ".checkboxText-2F08go")
                    )
                    if has_agree > 0:
                        driver.find_element(
                            By.CSS_SELECTOR, ".checkboxText-2F08go"
                        ).click()
                        driver.find_element(
                            By.CSS_SELECTOR, ".submitButton-34IPxt"
                        ).click()
                        logger.info(
                            f"Agreed to rules before reacting in {url} (id {id})"
                        )
                        time.sleep(1.5)

                success_verifying.append(link)
                update_obj = UpdateOne(
                    {"_id": link["_id"]},
                    {"$set": {"joined": True, "verified": True}},
                )

                # If necessary, go through steps to be able to talk by agreeing to the rules
                has_submit_rules = len(
                    driver.find_elements(
                        By.CSS_SELECTOR, ".button-cO0-d9 > .contents-3ca1mk"
                    )
                )
                if driver.execute_script(
                    "return (arguments[0] == 1)", has_submit_rules
                ):
                    driver.find_element(
                        By.CSS_SELECTOR, ".button-cO0-d9 > .contents-3ca1mk"
                    ).click()
                    driver.find_element(By.CSS_SELECTOR, ".checkboxText-2F08go").click()
                    driver.find_element(By.CSS_SELECTOR, ".submitButton-34IPxt").click()
                    logger.info(f"Agreed to rules in {url} (id {id})")

            except NoVerifyChannelException:
                logger.error(f"No verify channel found in {url} (id {id})")
            except Exception as e:
                logger.error(f"Error in attempting to verify in {url} (id {id})")
                # print(traceback.format_exc())

        if update_obj:
            updates.append(update_obj)
        time.sleep(30)

    driver.close()

    joined_urls = db.discord_link
    watchlist = db.watchlist

    try:
        watchlist_addition = watchlist.bulk_write(new_watchlist)
        invalid_results = joined_urls.bulk_write(invalid_links)
        logger.info(
            f"{invalid_results.modified_count} invite links were invalid! {watchlist_addition.inserted_count} have been added back to the watchlist."
        )
    except Exception:
        logger.error(
            f"Error in adding {len(new_watchlist)} entries to the watchlist and marking as invalid {len(invalid_links)} entries!"
        )
        return None

    try:
        joined_results = joined_urls.bulk_write(updates)
        logger.info(f"Joined {joined_results.modified_count} Discord servers!")

        logger.info(f"There were errors in joining {len(errors_joining)} servers.")
        logger.info(
            f"Out of {joined_results.modified_count} servers, we were able to verify in {len(success_verifying)}"
        )
    except Exception:
        logger.error(f"Error in marking {len(updates)} entries as joined.")
        return None

    return "Success"
