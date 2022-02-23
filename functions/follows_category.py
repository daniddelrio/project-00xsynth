import datetime
from pymongo import UpdateOne
import traceback
from pymongo import MongoClient
import os
from utils.custom_logger import setup_logger
from utils.mongo_client import db

logger = setup_logger("follows_category")


def handler(event, context):
    timestamp = datetime.datetime.utcnow()
    data = db.temp_followed

    discord_links = []
    watchlist = []

    for account in data.find():
        discord_urls = []
        if "entities" not in account:
            continue

        entities = account["entities"]
        account_id = account["id"]

        try:
            if "url" in entities and "urls" in entities["url"]:
                for url in entities["url"]["urls"]:
                    if (
                        "discord.gg" in url["display_url"]
                        and url["expanded_url"] not in discord_urls
                    ):
                        discord_urls.append(url["expanded_url"])

            if "description" in entities and "urls" in entities["description"]:
                for url in entities["description"]["urls"]:
                    if (
                        "discord.gg" in url["display_url"]
                        and url["expanded_url"] not in discord_urls
                        and url["display_url"] != "discord.gg"
                    ):
                        discord_urls.append(url["expanded_url"])

            if len(discord_urls) > 0:
                logger.info(f"Found Discord URLs for user {account_id}")
                discord_urls = [
                    UpdateOne(
                        {"url": url},
                        {
                            "$setOnInsert": {
                                "account_id": account["id"],
                                "url": url,
                                "joined": False,
                                "verified": False,
                                "valid": True,
                                "created_at": timestamp,
                            }
                        },
                        upsert=True,
                    )
                    for url in discord_urls
                ]
                discord_links.extend(discord_urls)
            else:
                logger.info(f"Added user {account_id} to watchlist")
                watchlist.append(
                    UpdateOne(
                        {"account_id": account["id"]},
                        {
                            "$setOnInsert": {
                                "account_id": account["id"],
                                "timestamp": timestamp,
                            }
                        },
                        upsert=True,
                    )
                )
        except Exception:
            logger.error(f"There was an error in categorizing user {account_id}")

    try:
        if len(watchlist) > 0:
            watchlist_collection = db.watchlist
            watchlist_results = watchlist_collection.bulk_write(watchlist)
            logger.info(
                f"Added {watchlist_results.upserted_count} entries to watchlist!"
            )
        else:
            logger.warning(f"No entries were added entries to watchlist.")
    except Exception:
        logger.error(f"Error in adding {len(watchlist)} entries to watchlist!")
        return None

    try:
        if len(discord_links) > 0:
            links_collection = db.discord_link
            discord_results = links_collection.bulk_write(discord_links)
            logger.info(
                f"Added {discord_results.upserted_count} entries to discord_link!"
            )
        else:
            logger.warning(f"No entries were added entries to discord_link.")
    except Exception:
        logger.error(f"Error in adding {len(discord_links)} entries to discord_link!")
        return None

    try:
        logger.info(
            f"Removing the {data.estimated_document_count()} entries in temp_followed"
        )
        data.drop()
        return { "message": "Success" }
    except Exception:
        logger.error(
            f"There was an error in removing the {data.estimated_document_count()} entries from temp_followed!"
        )
        return None
