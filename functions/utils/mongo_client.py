from pymongo import MongoClient
import os

MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DATABASE]
