import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')
MONGODB_URI = os.environ.get('MONGODB_URI')
user_id = '1465764550003904520'
r = requests.get(
    f'https://api.twitter.com/2/users/{user_id}/following', headers={'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'})

print(r.json())

mongo_client = MongoClient(MONGODB_URI)
