import os
from configparser import ConfigParser
# This file is so that we don't have to initialize a new database connection every time we call the Lambda function.

# Create the config file that contains the details pertaining to the channel we'll broadcast to.
def set_config(path):
  config = ConfigParser()
  config['telegram'] = {
    'token': os.environ['TELEGRAM_TOKEN'],
    'chat_id': os.environ['TELEGRAM_CHAT_ID'],
  }

  with open(path, 'w') as config_file:
    config.write(config_file)

  return path

config_path = set_config(os.environ['TELEGRAM_CONF_PATH'])