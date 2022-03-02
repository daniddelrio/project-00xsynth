import telegram_send
import os
from utils.custom_logger import setup_logger
# This configures the connection to the Telegram channel which this bot broadcasts messages to.
from utils.telegram_client import config_path
from utils.mongo_client import db
from datetime import datetime

logger = setup_logger("tg_send")

# This function splits the list of all messages into smaller chunks to avoid the character limit.
def split_character_limit(updates):
  # Telegram character limit per message. Lowered it from 4096 to 3000 so that each
  # message doesn't look too cluttered.
  MESSAGE_CHAR_LIMIT = 3000
  timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

  all_messages = []
  curr_message = f"<b>{timestamp}</b> (1)"

  for update in updates:
    temp_message = curr_message + "\n\n\n" + update
    if len(temp_message) < MESSAGE_CHAR_LIMIT:
      curr_message = temp_message
    else:
      all_messages.append(curr_message)
      curr_message = f'<b>{timestamp}</b> ({len(all_messages)+1})\n\n\n{update}'
  
  if len(curr_message) > 0:
    all_messages.append(curr_message)
  
  return all_messages

# This function consolidates the scraped accounts in "temp_folloewd" and broadcasts them to the Telegram channel
def handler(event, context):
    data = db.temp_followed
    all_updates = []

    # Goes through all accounts in the "temp_followed" collection
    for account in data.find():
        account_id = account['id']
        input_type = account['type']

        # Changes the verb in the message according to if the input user liked or followed this account.
        if input_type == 'like':
          verb = 'liked'
        elif input_type == 'follow':
          verb = 'followed'

        try:
          """
          The message looks something like:
          @solbigbrain followed @NFTethics. twitter.com/@NFTethics. [insert bio here]

          The message then gets added to the all_updates list.
          """
          message = '@{} {} @{}. twitter.com/{}. {}'.format(
              account['input'],
              verb,
              account['username'],
              account['username'],
              account['description'] if 'description' in account else '',
              )
            
          all_updates.append(message)
          logger.info(f"Formed Telegram message for user {account_id}.")
        except Exception:
          logger.error(f"There was an error in forming the Telegram message for user {account_id}")
  
    try:
      # Calls this function, explained above
      all_messages = split_character_limit(all_updates)

      # Sends the messages to the Telegram channel
      telegram_send.send(messages=all_messages, conf=config_path, parse_mode="html")
      logger.info(
          f"Sent {len(all_messages)} messages with a total of {len(all_updates)} updates on Telegram!"
      )
      return { "message": "Success" }
    except Exception:
      logger.error(f"Error in sending {len(all_messages)} messages with a total of {len(all_updates)} updates on Telegram!")
      return None