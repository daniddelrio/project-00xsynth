import os
from pymongo import MongoClient
from airflow.decorators import task

from scrape_follows.main import scrape_follows as scrape_follows_import
from follows_category.main import categorize_follows as categorize_follows_import

from dotenv import load_dotenv
load_dotenv()


class ScrapePipeline:
    def __init__(self):
        self.twitter_token = os.environ.get('TWITTER_BEARER_TOKEN')
        MONGODB_URI = os.environ.get('MONGODB_URI')
        MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE')

        mongo_client = MongoClient(MONGODB_URI)
        self.db = mongo_client[MONGODB_DATABASE]

    @task(task_id="scrape_followed_of_inputs")
    def scrape_follows(self):
        return scrape_follows_import(self.twitter_token, self.db)

    @task(task_id="categorize_follows")
    def categorize_follows(self):
        return categorize_follows_import(self.db)
