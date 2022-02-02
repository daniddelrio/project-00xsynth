import os
import json
import datetime
import requests
import traceback
from pymongo import MongoClient
from utils.custom_logger import setup_logger
from utils.mongo_client import db

logger = setup_logger("track_watchlist")


def handler(event, context):
    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

    watchlist = db.watchlist
    discord_links = []
    newly_approved_old_ids = []
    timestamp = datetime.datetime.utcnow()
    for account in watchlist.find():
        account_id = account["account_id"]
        try:
            r = requests.get(
                f"https://api.twitter.com/2/users/{account_id}/tweets?tweet.fields=entities",
                headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
            )

            if "data" in r.json():
                tweets = r.json()["data"]

                discord_urls = []
                for tweet in tweets:
                    if "entities" in tweet and "urls" in tweet["entities"]:
                        for url in tweet["entities"]["urls"]:
                            if (
                                "discord.gg" in url["display_url"]
                                and url["display_url"] not in discord_urls
                            ):
                                discord_urls.append(url["expanded_url"])

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
            # print(traceback.format_exc())

    # Move from watchlist to approved_accounts
    try:
        links_collection = db.discord_link
        discord_results = links_collection.insert_many(discord_links)
        logger.info(
            f"Added {len(discord_results.inserted_ids)} new entries to discord_link!"
        )
    except Exception:
        logger.error(f"Error in adding {len(discord_links)} entries to discord_link!")
        return None

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
