import os
import json
import datetime
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE')
TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DATABASE]

watchlist = db.watchlist
newly_approved = []
newly_approved_old_ids = []
timestamp = datetime.datetime.utcnow()
for account in watchlist.find():
    account_id = account['account_id']
    r = requests.get(f'https://api.twitter.com/2/users/{account_id}/tweets?tweet.fields=entities', headers={
                     'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'})

    tweets = r.json()['data']

    discord_urls = []
    for tweet in tweets:
        if 'entities' in tweet and 'urls' in tweet['entities']:
            for url in tweet['entities']['urls']:
                if 'discord.gg' in url['display_url'] and url['display_url'] not in discord_urls:
                    discord_urls.append(url['expanded_url'])

    if len(discord_urls) > 0:
        discord_urls = [{'url': url, 'verified': False}
                        for url in discord_urls]
        newly_approved.append({
            'account_id': account['account_id'],
            'discord_urls': discord_urls,
            'timestamp': timestamp,
        })
        newly_approved_old_ids.append(account['_id'])

# Move from watchlist to approved_accounts

approved_collection = db.approved_account
approved_results = approved_collection.insert_many(newly_approved)
print(
    f"Added {len(approved_results.inserted_ids)} entries to approved_account!")

watchlist_deletion = watchlist.delete_many(
    {"_id": {"$in": newly_approved_old_ids}})
print(newly_approved_old_ids)
