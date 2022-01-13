import datetime
from pymongo import UpdateOne


def categorize_follows(db):
    timestamp = datetime.datetime.utcnow()
    data = db.temp_followed

    discord_links = []
    watchlist = []

    for account in data.find():
        discord_urls = []
        if 'entities' not in account:
            continue

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
            discord_urls = [UpdateOne(
                            {'url': url},
                            {"$setOnInsert": {
                                'account_id': account['id'],
                                'url': url,
                                'joined': False,
                                'verified': False,
                                'created_at': timestamp
                            }},
                            upsert=True)
                            for url in discord_urls]
            discord_links.extend(discord_urls)
        else:
            watchlist.append(
                UpdateOne({'account_id': account['id']},
                          {'$setOnInsert': {
                              'account_id': account['id'],
                              'timestamp': timestamp,
                          }},
                          upsert=True
                          ))
            # watchlist.append({
            #     'account_id': account['id'],
            #     'timestamp': timestamp,
            # })

    watchlist_collection = db.watchlist
    watchlist_results = watchlist_collection.bulk_write(watchlist)
    print(f"Added {watchlist_results.upserted_count} entries to watchlist!")

    links_collection = db.discord_link
    discord_results = links_collection.bulk_write(discord_links)
    print(
        f"Added {discord_results.upserted_count} entries to discord_link!")

    data.drop()
