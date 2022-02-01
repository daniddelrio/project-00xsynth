from pymongo import MongoClient
import requests
from pymongo import UpdateOne
import traceback
import os


def handler(event, context):
    MONGODB_URI = os.environ.get("MONGODB_URI")
    MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")
    TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DATABASE]

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
                print(traceback.format_exc())

    temp_follows = db.temp_followed
    followed_results = temp_follows.bulk_write(liked_accounts)
    print(
        f"Added {followed_results.upserted_count} entries to temp_followed (based on liked tweets)!"
    )
