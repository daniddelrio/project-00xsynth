from pymongo import MongoClient
import requests
from pymongo import UpdateOne
import traceback
import os
from custom_logger import setup_logger

logger = setup_logger("scrape_liked")


def handler(event, context):
    MONGODB_URI = os.environ.get("MONGODB_URI")
    MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")
    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

    try:
        mongo_client = MongoClient(MONGODB_URI)
        db = mongo_client[MONGODB_DATABASE]
    except Exception:
        logger.error("Could not connect to MongoDB database")
        return None

    inputs = db.input
    liked_accounts = []
    # Put all scraped followed accts into one temp collection.
    for input in inputs.find():
        account_id = input["account_id"]
        if account_id:
            try:
                r = requests.get(
                    f"https://api.twitter.com/2/users/{account_id}/liked_tweets?user.fields=id,description,entities,created_at&expansions=author_id",
                    headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
                )
                res = r.json()
                if "includes" in res and "users" in res["includes"]:
                    users_len = len(res["includes"]["users"])
                    logger.info(
                        f"Adding {users_len} accounts who follow user {account_id} to temp_follows"
                    )
                    liked_accounts.extend(
                        [
                            UpdateOne(
                                {"id": follow["id"]},
                                {"$setOnInsert": follow},
                                upsert=True,
                            )
                            for follow in res["includes"]["users"]
                        ]
                    )
            except:
                logger.error(
                    "There was an error in scraping the likes of user {account_id}"
                )
                # print(traceback.format_exc())

    try:
        temp_follows = db.temp_followed
        followed_results = temp_follows.bulk_write(liked_accounts)
        logger.info(
            f"Added {followed_results.upserted_count} unique entries to temp_followed (based on liked tweets)!"
        )
        return "Success"
    except Exception:
        logger.error(
            f"Error in adding {len(liked_accounts)} entries to temp_followed (based on liked tweets)!"
        )
        return None
