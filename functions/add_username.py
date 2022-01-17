import datetime
import os
import requests
from pymongo import MongoClient
import traceback
from dotenv import load_dotenv
load_dotenv()

MONGODB_URI = os.environ.get('AIRFLOW_VAR_MONGODB_URI')
MONGODB_DATABASE = os.environ.get('AIRFLOW_VAR_MONGODB_DATABASE')
TWITTER_BEARER_TOKEN = os.environ.get('AIRFLOW_VAR_TWITTER_BEARER_TOKEN')

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DATABASE]

username = input('Enter Twitter username: ')
get_more_input = ''
while True:
    try:
        r = requests.get(
            f'https://api.twitter.com/2/users/by/username/{username}', headers={'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'})

        if 'data' in r.json():
            account_id = r.json()['data']['id']

            timestamp = datetime.datetime.utcnow()
            input = {"username": username,
                     "account_id": account_id,
                     "timestamp": timestamp,
                     "has_been_scraped": False,
                     }
            inputs = db.input
            inserted_id = inputs.insert_one(input).inserted_id

            print("Created: " + str(inserted_id))
        else:
            print(f'Could not find user @{username}')
    except:
        print(traceback.format_exc())

    get_more_input = input('Add another user? (Y/N): ')
    if get_more_input.lower() != 'y':
        break

    username = input('Enter Twitter username: ')
