import datetime
from pymongo import UpdateOne
from utils.custom_logger import setup_logger
from utils.mongo_client import db

logger = setup_logger("follows_category")


# This function categorizes all the scraped accouunts in the "temp_followed" collection according to if they have a Discord URL in their bios.
def handler(event, context):
    timestamp = datetime.datetime.utcnow()
    data = db.temp_followed

    discord_links = []
    watchlist = []

    # Go through all accounts in the temp_followed collection
    # You can check the sample_data/follows_category.json file for sample data in temp_followed.
    for account in data.find():
        discord_urls = []
        # No "entities" in the account object means there are no URLs in the bio
        if "entities" not in account:
            continue

        entities = account["entities"]
        account_id = account["id"]

        try:
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

            if len(discord_urls) > 0:
                # If there were discord URLs, add it to the "discord_urls" collection
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
                # If there weren't any, add the account to the "watchlist" collection
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
        # Add the entries in the watchlist to the "watchlist" collection
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
        # Add the links found to the "discord_links" collection
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
        # Delete everything in "temp_followed" collection
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
