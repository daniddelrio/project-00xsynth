import telegram_send
import os
from utils.custom_logger import setup_logger
from utils.telegram_client import config_path
from utils.mongo_client import db
from datetime import datetime

logger = setup_logger("tg_send")

def split_character_limit(updates):
  # Telegram character limit per message. Lowered it from 4096 to 3000.
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

def handler(event, context):
    data = db.temp_followed
    all_updates = []

    for account in data.find():
        account_id = account['id']
        input_type = account['type']

        if input_type == 'like':
          verb = 'liked'
        elif input_type == 'follow':
          verb = 'followed'

        try:
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
      all_messages = split_character_limit(all_updates)
      telegram_send.send(messages=all_messages, conf=config_path, parse_mode="html")
      logger.info(
          f"Sent {len(all_messages)} messages with a total of {len(all_updates)} updates on Telegram!"
      )
      return "Success"
    except Exception:
      logger.error(f"Error in sending {len(all_messages)} messages with a total of {len(all_updates)} updates on Telegram!")
      return None