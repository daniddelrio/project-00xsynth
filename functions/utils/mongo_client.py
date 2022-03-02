from pymongo import MongoClient
import os

# This file is so that we don't have to initialize a new database connection every time we call the Lambda function.

MONGODB_URI = os.environ.get("MONGODB_URI")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DATABASE]
