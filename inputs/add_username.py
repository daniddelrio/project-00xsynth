import datetime
import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

MONGODB_URI = os.environ.get('MONGODB_URI')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE')
TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DATABASE]

username = input('Enter Twitter username: ')
r = requests.get(
    f'https://api.twitter.com/2/users/by/username/{username}', headers={'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'})
account_id = r.json()['data']['id']

timestamp = datetime.datetime.utcnow()
input = {"username": username,
         "account_id": account_id,
         "timestamp": timestamp}
inputs = db.input
inserted_id = inputs.insert_one(input).inserted_id

print("Created: " + str(inserted_id))
