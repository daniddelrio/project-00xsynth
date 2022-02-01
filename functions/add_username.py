import datetime
import os
import requests
from pymongo import MongoClient
import traceback
from dotenv import load_dotenv
from custom_logger import setup_logger

logger = setup_logger("add_username")


def handler(event, context):
    if "Username" not in event:
        logger.error(f"No username was given.")
        return None

    MONGODB_URI = os.environ.get("MONGODB_URI")
    MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")
    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DATABASE]

    username = event["Username"]

    try:
        r = requests.get(
            f"https://api.twitter.com/2/users/by/username/{username}",
            headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
        )

        if "data" in r.json():
            account_id = r.json()["data"]["id"]

            timestamp = datetime.datetime.utcnow()
            input = {
                "username": username,
                "account_id": account_id,
                "timestamp": timestamp,
                "has_been_scraped": False,
            }
            inputs = db.input
            inserted_id = inputs.insert_one(input).inserted_id

            logger.info(
                f"Created user with username {username}, now with ID {str(inserted_id)}"
            )
            return {"id": inserted_id, "username": username}
        else:
            logger.info(f"Could not find user @{username}")
            return None
    except:
        logger.error("An error occurred while adding the username.")
        return None
