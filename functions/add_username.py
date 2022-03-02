import datetime
import os
import requests
from utils.custom_logger import setup_logger
from utils.mongo_client import db

logger = setup_logger("add_username")


# This function allows you to add the usernames of accounts that you want to track.
def handler(event, context):
    """
    A field named Username must be in the "event" JSON object.

    Example event:
    {
        "Username": "addusernamehere"
    }
    """
    if "Username" not in event:
        logger.error(f"No username was given.")
        return None

    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

    username = event["Username"]

    try:
        # Make a request to the Twitter API (username endpoint)
        r = requests.get(
            f"https://api.twitter.com/2/users/by/username/{username}",
            headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
        )

        # Checks if there is a user with the given username
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
            # Add the given account to the "input" collection in MongoDB
            inserted_id = inputs.insert_one(input).inserted_id

            logger.info(
                f"Created user with username {username}, now with ID {str(inserted_id)}"
            )
            return {"id": str(inserted_id), "username": username}
        else:
            logger.info(f"Could not find user @{username}")
            return None
    except:
        logger.error("An error occurred while adding the username.")
        return None
