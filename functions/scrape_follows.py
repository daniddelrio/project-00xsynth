import requests
from pymongo import UpdateOne
import os
from utils.custom_logger import setup_logger
from utils.mongo_client import db

logger = setup_logger("scrape_follows")


# This function scrapes the accounts that the input accounts follow and adds them to the "temp_followed" collection.
def handler(event, context):
    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
    MAX_RESULTS_FOR_SCRAPED = 50
    MAX_RESULTS_FOR_NEW = 100

    inputs = db.input
    followed_accounts = []
    updated_accounts = []
    # Put all scraped followed accounts into one temp collection.
    for input in inputs.find():
        account_id = input["account_id"]
        username = input["username"]
        if account_id:
            try:
                # If it's already been scraped before, then we can just get the last 15 followed accounts of the person
                has_been_scraped = input["has_been_scraped"]

                if has_been_scraped:
                    # Gets the last 50 followed accounts and adds them to the followed_accounts list
                    r = requests.get(
                        f"https://api.twitter.com/2/users/{account_id}/following?user.fields=created_at,entities,description&max_results={MAX_RESULTS_FOR_SCRAPED}",
                        headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
                    )
                    res = r.json()
                    if "data" in res:
                        data_len = len(res["data"])
                        followed_accounts.extend(
                            [
                                UpdateOne(
                                    {"id": follow["id"]},
                                    {"$setOnInsert": {**follow, 'type': 'follow', 'input': username, 'source_id': account_id}},
                                    upsert=True,
                                )
                                for follow in res["data"]
                            ]
                        )
                        logger.info(
                            f"Adding {data_len} accounts who follow user {account_id} to temp_follows"
                        )
                else:
                    # If it hasn't been scraped, we get all the followed accounts of the user using the pagination_tokens returned.
                    # RATE LIMIT: 15 requests / 15 minutes
                    next_token = "next"
                    while next_token:
                        pagination_token = (
                            f"pagination_token={next_token}"
                            if next_token != "next"
                            else ""
                        )
                        # Gets the last 100 followed accounts with the given pagination_token
                        r = requests.get(
                            f"https://api.twitter.com/2/users/{account_id}/following?user.fields=created_at,entities,description&max_results={MAX_RESULTS_FOR_NEW}&{pagination_token}",
                            headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
                        )

                        res = r.json()
                        # Updates the token for the next page of followed accounts
                        next_token = res["next_token"] if "next_token" in res else None
                        if "data" in res:
                            data_len = len(res["data"])
                            logger.info(
                                f"Adding {data_len} more accounts who follow user {account_id} to temp_follows"
                            )
                            followed_accounts.extend(
                                [
                                    UpdateOne(
                                        {"id": follow["id"]},
                                        {"$setOnInsert": {**follow, 'type': 'follow', 'input': username, 'source_id': account_id}},
                                        upsert=True,
                                    )
                                    for follow in res["data"]
                                ]
                            )

                    # This will update this current account to mark "has_been_scraped" as True so that we
                    # don't have to scrape all the followed accounts again
                    updated_accounts.append(
                        UpdateOne(
                            {"_id": input["_id"]},
                            {
                                "$set": {
                                    "has_been_scraped": True,
                                }
                            },
                        )
                    )
            except:
                logger.error(
                    "There was an error in scraping the following of user {account_id}"
                )

    try:
        # Add the scraped accounts to the "temp_followed" collection
        temp_follows = db.temp_followed
        followed_results = temp_follows.bulk_write(followed_accounts)
        logger.info(
            f"Added {followed_results.upserted_count} total entries to temp_followed!"
        )
    except Exception:
        logger.error(
            f"Error in adding {len(followed_accounts)} entries to temp_followed!"
        )
        return None

    # Updates the "has_been scraped" field of the newly scraped accounts
    if len(updated_accounts) > 0:
        try:
            db.input.bulk_write(updated_accounts)
        except Exception:
            logger.error(
                f"Error in updating {len(updated_accounts)} entries in the inputs collection."
            )
            return None

    return { "message": "Success" }