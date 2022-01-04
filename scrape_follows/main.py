import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')
MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE')

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DATABASE]

inputs = db.input
for input in inputs.find():
    account_id = input['account_id']
    if account_id:
        r = requests.get(
            f'https://api.twitter.com/2/users/{account_id}/following?user.fields=created_at,entities,description',
            headers={'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'})
        print(r.json())
