import os
import json
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE')

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DATABASE]

with open('sample.json') as json_file:
    timestamp = datetime.datetime.utcnow()
    data_dict = json.load(json_file)
    data = data_dict['data']

    approved_accounts = []
    watchlist = []

    for account in data:
        discord_urls = []
        entities = account['entities']

        if 'url' in entities and 'urls' in entities['url']:
            for url in entities['url']['urls']:
                if 'discord.gg' in url['display_url'] and url['expanded_url'] not in discord_urls:
                    discord_urls.append(url['expanded_url'])

        if 'description' in entities and 'urls' in entities['description']:
            for url in entities['description']['urls']:
                if 'discord.gg' in url['display_url'] and url['expanded_url'] not in discord_urls:
                    discord_urls.append(url['expanded_url'])

        if len(discord_urls) > 0:
            discord_urls = [{'url': url, 'verified': False}
                            for url in discord_urls]
            approved_accounts.append({
                'account_id': account['id'],
                'discord_urls': discord_urls,
                'timestamp': timestamp,
            })
        else:
            watchlist.append({
                'account_id': account['id'],
                'timestamp': timestamp,
            })

    watchlist_collection = db.watchlist
    watchlist_results = watchlist_collection.insert_many(watchlist)
    print(f"Added {len(watchlist_results.inserted_ids)} entries to watchlist!")

    approved_collection = db.approved_account
    approved_results = approved_collection.insert_many(approved_accounts)
    print(
        f"Added {len(approved_results.inserted_ids)} entries to approved_account!")
