import os
import json
import datetime
import requests
import traceback
from pymongo import MongoClient


def handler(event, context):
    MONGODB_URI = os.environ.get("MONGODB_URI")
    MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")
    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DATABASE]

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
            print(traceback.format_exc())

    # Move from watchlist to approved_accounts
    links_collection = db.discord_link
    discord_results = links_collection.insert_many(discord_links)
    print(f"Added {len(discord_results.inserted_ids)} new entries to discord_link!")

    watchlist_deletion = watchlist.delete_many({"_id": {"$in": newly_approved_old_ids}})
    print(newly_approved_old_ids)
