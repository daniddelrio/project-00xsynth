import os
from configparser import ConfigParser

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