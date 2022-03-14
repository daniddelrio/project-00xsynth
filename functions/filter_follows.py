import requests
import datetime
import os
from utils.custom_logger import setup_logger
from utils.mongo_client import db
from pymongo import UpdateOne

logger = setup_logger("filter_follows")

"""
This function filters our temp_followed so that we only keep the ones we haven't scraped before.

Steps:
1. temp_follows = Group A
2. Get all entries of latest_follows_per_user (which are already grouped by source_id) = Group B
3. For all entries of Group A, check if they're in Group B.
4. If an element isn't in Group B, we add to Group B and eject the last element of the list in Group B.
5. If an element IS in Group B, then we remove it from temp_follows.
"""
def handler(event, context):
    # Max length of the follows_ids list
    MAX_RESULTS = 150
  
    latest_follows_per_user = db.latest_follows_per_user.find()
    latest_follows_per_user = {follow['source_id']: follow['follows_ids'] for follow in latest_follows_per_user}
    # This is what we'll update as we find new follows that will evict the oldest follow in latest_follows_per_user for this user
    new_latest_follows_per_user = latest_follows_per_user.copy()

    temp_followed = db.temp_followed
    temp_followed_count = temp_followed.count_documents({})
    
    # List of temp_followed entries that we'll keep
    new_temp_followed = []
    for user in temp_followed.find():
        user_id = user['id']
        # source_id = source user which we got this new user from (e.g. source_user followed this current user)
        source_id = user['source_id']
        # This means that we haven't scraped this user before
        if source_id not in latest_follows_per_user or user_id not in latest_follows_per_user[source_id]:
          # If we never scraped the source user before, we initialize a new entry for them
          if source_id not in latest_follows_per_user:
            new_latest_follows_per_user[source_id] = []
            latest_follows_per_user[source_id] = []
          # We evict the last one ONLY if we've exceeded our MAX_RESULTS
          elif len(new_latest_follows_per_user[source_id]) >= MAX_RESULTS:
            new_latest_follows_per_user[source_id].pop()
          # Update latest_follows_per_user with this newest account
          new_latest_follows_per_user[source_id].insert(0, user_id)

          # We only add to new_temp_followed if it follows our initial conditions (i.e. we haven't scraped this user before)
          new_temp_followed.append(user)

          logger.info(
              f"Scraped new user {user['username']} from {user['input']}!"
          )
    
    # Convert new_latest_follows_per_user dict back to the original form in the database
    timestamp = datetime.datetime.utcnow()
    new_latest_follows_per_user = [UpdateOne(
                                    {"source_id": source_id},
                                    {"$set": {'follows_ids': follows_ids, 'timestamp': timestamp}},
                                    upsert=True,
                                  ) for source_id, follows_ids in new_latest_follows_per_user.items()]
    
    try:
        # Replace the temp_followed with the new_temp_followed
        logger.info(f"Just dropped {temp_followed_count} temp_followed entries, to make way for the filtered temp_followed...")
        temp_followed.drop()
        if len(new_temp_followed) > 0:
          followed_results = temp_followed.insert_many(new_temp_followed)
          logger.info(f"Added {len(new_temp_followed)} new temp_followed entries, so that we include only those we haven't scraped!")
        else:
          logger.warning(f"Adding no new entries to temp_followed, so we don't have any new follows!")
    except Exception:
        logger.error(
            f"Error in dropping {temp_followed_count} entries and adding the {len(new_temp_followed)} unscraped temp_followed entries!"
        )
        return None

    try:
        # Update our latest_follows_per_user with the new list where we add our new accounts and evict old ones
        collection = db.latest_follows_per_user
        latest_follow_results = collection.bulk_write(new_latest_follows_per_user)
        logger.info(f"Updated {latest_follow_results.matched_count + latest_follow_results.upserted_count} entries in latest_follows_per_user!")
    except Exception:
        logger.error(
            f"Error in updating the latest_follows_per_user collection!"
        )
        return None

    return { "message": "Success" }