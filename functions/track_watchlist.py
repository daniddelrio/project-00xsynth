import os
import datetime
import requests
from utils.custom_logger import setup_logger
from utils.mongo_client import db

logger = setup_logger("track_watchlist")


# This function checks the watchlist if they've either updated their description with a new Discord bio
# or they've posted a new tweet that contains a Discord URL.

def handler(event, context):
    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
    MAX_RESULTS = 20

    watchlist = db.watchlist
    discord_links = []
    newly_approved_old_ids = []
    timestamp = datetime.datetime.utcnow()
    # Goes through all accounts in the watchlist.
    # Refer to the sample_data/track_watchlist.json for what the watchlist data looks like.
    for account in watchlist.find():
        account_id = account["account_id"]
        try:
            # This API call gets the latest 20 tweets made by the user.
            r = requests.get(
                f"https://api.twitter.com/2/users/{account_id}/tweets?tweet.fields=entities&max_results={MAX_RESULTS}",
                headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
            )
            # This API call gets the user's information (e.g. user bio)
            r_user = requests.get(
                f"https://api.twitter.com/2/users/{account_id}?user.fields=entities",
                headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
            )

            discord_urls = []
            r_user_data = r_user.json()
            # We first check the user's info
            if "data" in r_user_data and 'entities' in r_user_data['data']:
                entities = r_user_data['data']['entities']
                # Check if there are Discord URLs in the user's attached URL
                if "url" in entities and "urls" in entities["url"]:
                    for url in entities["url"]["urls"]:
                        if (
                            "discord.gg" in url["display_url"]
                            and url["expanded_url"] not in discord_urls
                        ):
                            discord_urls.append(url["expanded_url"])

                # Check if there are Discord URLs in the user's bio
                if "description" in entities and "urls" in entities["description"]:
                    for url in entities["description"]["urls"]:
                        if (
                            "discord.gg" in url["display_url"]
                            and url["expanded_url"] not in discord_urls
                            and url["display_url"] != "discord.gg"
                        ):
                            discord_urls.append(url["expanded_url"])
            
            # We then check the user's tweets if they tweeted a Discord URL
            if "data" in r.json():
                tweets = r.json()["data"]

                for tweet in tweets:
                    if "entities" in tweet and "urls" in tweet["entities"]:
                        for url in tweet["entities"]["urls"]:
                            if (
                                "discord.gg" in url["display_url"]
                                and url["display_url"] not in discord_urls
                            ):
                                discord_urls.append(url["expanded_url"])

            # If there were discord URLs, add it to the "discord_urls" collection and remove from "watchlist".
            if len(discord_urls) > 0:
                logger.info(f"Found Discord URLs for user {account_id}")
                discord_urls = [
                    {
                        "account_id": account["account_id"],
                        "url": url,
                        "joined": False,
                        "verified": False,
                        "created_at": timestamp,
                    }
                    for url in discord_urls
                ]
                discord_links.extend(discord_urls)
                newly_approved_old_ids.append(account["_id"])
        except Exception as e:
            logger.error(f"There was an error in tracking user {account_id}")

    # Add the links found to the "discord_links" collection
    try:
        links_collection = db.discord_link
        discord_results = links_collection.insert_many(discord_links)
        logger.info(
            f"Added {len(discord_results.inserted_ids)} new entries to discord_link!"
        )
    except Exception:
        logger.error(f"Error in adding {len(discord_links)} entries to discord_link!")
        return None

    # For the accounts in the watchlist where we found a Discord URL, remove them from the watchlist
    try:
        watchlist_deletion = watchlist.delete_many(
            {"_id": {"$in": newly_approved_old_ids}}
        )
        logger.info(f"Deleted {len(newly_approved_old_ids)} entries from watchlist!")
    except Exception:
        logger.error(
            f"Error in deleting {len(newly_approved_old_ids)} entries from watchlist!"
        )
        return None
    
    return { "message": "Success" }