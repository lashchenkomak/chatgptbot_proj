import telebot
import openai
from utils import start_command, handle_selection, handle_photo, handle_text
import logging
import os
from dotenv import load_dotenv

load_dotenv()
my_api_key = os.getenv('API_KEY')
my_bot_key = os.getenv('BOT_KEY')

bot = telebot.TeleBot(my_bot_key)
openai.api_key = my_api_key

logger = logging.getLogger('ChatGPT_bot')
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('bot.log')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

custom_des = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(custom_des)
console_handler.setFormatter(custom_des)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    start_command(bot, message, user_data, logger)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    handle_selection(bot, call, user_data, logger)

@bot.message_handler(content_types=['photo'])
def photo(message):
    handle_photo(bot, message, user_data, logger)

@bot.message_handler(func=lambda message: True)
def text(message):
    handle_text(bot, message, user_data, logger)


bot.polling(none_stop=True)
