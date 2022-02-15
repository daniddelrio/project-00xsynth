from distutils.command.config import config
import telegram_send
import os
from utils.custom_logger import setup_logger
from utils.telegram_client import config_path
from utils.mongo_client import db

logger = setup_logger("tg_send")

def handler(event, context):
    data = db.temp_followed
    all_messages = []
    telegram_send.send(messages=["test"], conf=config_path)

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
            
          all_messages.append(message)
          logger.info(f"Formed Telegram message for user {account_id}.")
        except Exception:
          logger.error(f"There was an error in forming the Telegram message for user {account_id}")
  
    try:
      telegram_send.send(messages=all_messages, conf=config_path)
      logger.info(
          f"Sent {len(all_messages)} messages on Telegram!"
      )
    except Exception:
      logger.error(f"Error in sending {len(all_messages)} messages on Telegram!")
