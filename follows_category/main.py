import datetime
from pymongo import UpdateOne


def categorize_follows(db):
    timestamp = datetime.datetime.utcnow()
    data = db.temp_followed

    approved_accounts = []
    watchlist = []

    for account in data.find():
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
            approved_accounts.append(
                UpdateOne({'account_id': account['id']},
                          {'$setOnInsert': {
                              'account_id': account['id'],
                              'discord_urls': discord_urls,
                              'timestamp': timestamp,
                          }},
                          upsert=True
                          ))
            # approved_accounts.append({
            #     'account_id': account['id'],
            #     'discord_urls': discord_urls,
            #     'timestamp': timestamp,
            # })
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

    approved_collection = db.approved_account
    approved_results = approved_collection.bulk_write(approved_accounts)
    print(
        f"Added {approved_results.upserted_count} entries to approved_account!")

    data.drop()
