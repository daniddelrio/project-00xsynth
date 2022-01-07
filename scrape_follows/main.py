import requests
import os
from pymongo import UpdateOne


def scrape_follows(twitter_token, db):
    inputs = db.input
    followed_accounts = []
    updated_accounts = []
    # Put all scraped followed accts into one temp collection.
    for input in inputs.find():
        account_id = input['account_id']
        if account_id:
            has_been_scraped = input['has_been_scraped']

            if has_been_scraped:
                r = requests.get(
                    f'https://api.twitter.com/2/users/{account_id}/following?user.fields=created_at,entities,description&max_results=15',
                    headers={'Authorization': f'Bearer {twitter_token}'})
                res = r.json()
                # followed_accounts.extend(res['data'])
                followed_accounts.extend([UpdateOne({'id': follow['id']},
                                                    {'$setOnInsert': follow},
                                                    upsert=True
                                                    ) for follow in res['data']])
            else:
                # RATE LIMIT: 15 requests / 15 minutes
                next_token = 'next'
                while next_token:
                    pagination_token = f'pagination_token={next_token}' if next_token != 'next' else ''
                    r = requests.get(
                        f'https://api.twitter.com/2/users/{account_id}/following?user.fields=created_at,entities,description&max_results=100&{pagination_token}',
                        headers={'Authorization': f'Bearer {twitter_token}'})

                    res = r.json()
                    next_token = res['next_token'] if 'next_token' in res else None
                    # followed_accounts.extend(res['data'])
                    followed_accounts.extend([UpdateOne({'id': follow['id']},
                                                        {'$setOnInsert': follow},
                                                        upsert=True
                                                        ) for follow in res['data']])

                updated_accounts.append(
                    UpdateOne({'_id': input['_id']},
                              {'$set': {
                                  'has_been_scraped': True,
                              }},
                              ))

    temp_follows = db.temp_followed
    followed_results = temp_follows.bulk_write(followed_accounts)
    print(
        f"Added {followed_results.upserted_count} entries to temp_followed!")

    if len(updated_accounts) > 0:
        db.input.bulk_write(updated_accounts)
