import requests
from pymongo import UpdateOne
import os
from utils.custom_logger import setup_logger
from utils.mongo_client import db

logger = setup_logger("scrape_liked")


# This function scrapes the accounts of the tweets that the input accounts like and adds them to the "temp_followed" collection.
def handler(event, context):
    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
    MAX_RESULTS = 20

    inputs = db.input
    liked_accounts = []
    # Put all scraped liked accts into one temp collection.
    for input in inputs.find():
        account_id = input["account_id"]
        username = input["username"]
        if account_id:
            try:
                # Gets the latest 20 tweets that the account liked.
                r = requests.get(
                    f"https://api.twitter.com/2/users/{account_id}/liked_tweets?user.fields=id,description,entities,created_at&expansions=author_id&max_results={MAX_RESULTS}",
                    headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
                )
                res = r.json()
                # Adds the account of the liked tweet to "temp_followed" collection
                if "includes" in res and "users" in res["includes"]:
                    users_len = len(res["includes"]["users"])
                    logger.info(
                        f"Adding {users_len} accounts who follow user {account_id} to temp_follows"
                    )
                    liked_accounts.extend(
                        [
                            UpdateOne(
                                {"id": follow["id"]},
                                {"$setOnInsert": {**follow, 'type': 'like', 'input': username, 'source_id': account_id}},
                                upsert=True,
                            )
                            for follow in res["includes"]["users"]
                        ]
                    )
            except:
                logger.error(
                    "There was an error in scraping the likes of user {account_id}"
                )

    try:
        # Add the scraped accounts to the "temp_followed" collection
        temp_follows = db.temp_followed
        followed_results = temp_follows.bulk_write(liked_accounts)
        logger.info(
            f"Added {followed_results.upserted_count} unique entries to temp_followed (based on liked tweets)!"
        )
        return { "message": "Success" }
    except Exception:
        logger.error(
            f"Error in adding {len(liked_accounts)} entries to temp_followed (based on liked tweets)!"
        )
        return None
