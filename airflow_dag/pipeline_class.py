from airflow.models import Variable
import os
from pymongo import MongoClient
from airflow.decorators import task

from project_00xsynth.scrape_follows.main import scrape_follows as scrape_follows_import
from project_00xsynth.follows_category.main import categorize_follows as categorize_follows_import
from project_00xsynth.track_watchlist.main import track_watchlist as track_watchlist_import
from project_00xsynth.join_discord.discord import join_discord as join_discord_import

from dotenv import load_dotenv
load_dotenv()


@task(task_id="scrape_followed_of_inputs")
def scrape_follows():
    twitter_token = Variable.get('twitter_bearer_token')
    MONGODB_URI = Variable.get('mongodb_uri')
    MONGODB_DATABASE = Variable.get('mongodb_database')

    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DATABASE]

    return scrape_follows_import(twitter_token, db)


@task(task_id="categorize_follows")
def categorize_follows():
    MONGODB_URI = Variable.get('mongodb_uri')
    MONGODB_DATABASE = Variable.get('mongodb_database')

    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DATABASE]

    return categorize_follows_import(db)


@task(task_id="track_watchlist")
def track_watchlist():
    twitter_token = Variable.get('twitter_bearer_token')
    MONGODB_URI = Variable.get('mongodb_uri')
    MONGODB_DATABASE = Variable.get('mongodb_database')

    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DATABASE]

    return track_watchlist_import(twitter_token, db)


@task(task_id="join_discord")
def join_discord():
    discord_email = Variable.get('discord_email')
    discord_password = Variable.get('discord_password')
    MONGODB_URI = Variable.get('mongodb_uri')
    MONGODB_DATABASE = Variable.get('mongodb_database')

    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client[MONGODB_DATABASE]

    return join_discord_import(discord_email, discord_password, db)
