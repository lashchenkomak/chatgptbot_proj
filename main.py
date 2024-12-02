import telebot
import openai
import time
from utils import create_role_buttons, create_model_buttons, send_role_image, extract_text_from_image
from messages import WELCOME_MESSAGE, ROLE_MESSAGES, ROLE_SELECTED_MESSAGE, MODEL_SELECTED_MESSAGES
from constants import GPT_MODELS
import logging
from dotenv import load_dotenv
import os

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
def start_command(message):
    user_data[message.chat.id] = {'user_model': '', 'user_role': '', 'user_history': []}
    bot.send_message(message.chat.id, WELCOME_MESSAGE, reply_markup=create_role_buttons())
    logger.info(f'User {message.chat.id} started the bot.')

@bot.callback_query_handler(func=lambda call: True)
def handle_selection(call):
    chat_id = call.message.chat.id
    user_info = user_data.get(chat_id)

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    bot.delete_message(chat_id, call.message.message_id)

    if call.data in ROLE_MESSAGES:
        user_info['user_role'] = call.data
        logger.info(f'User {chat_id} selected role: {call.data}')

        time.sleep(1)
        bot.send_message(chat_id, ROLE_MESSAGES[call.data])
        send_role_image(bot, chat_id, call.data)

        time.sleep(1)
        role_message = bot.send_message(chat_id, ROLE_SELECTED_MESSAGE, reply_markup=create_model_buttons())
        user_info['role_message_id'] = role_message.message_id
    elif call.data in GPT_MODELS:
        user_info['user_model'] = call.data
        logger.info(f'User {chat_id} selected model: {call.data}')

        time.sleep(1)
        bot.send_message(chat_id, MODEL_SELECTED_MESSAGES[call.data])

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    user_info = user_data.get(chat_id)

    if not user_info or not user_info['user_model']:
        bot.send_message(chat_id, 'Please select a role and model first.')
        logger.warning(f'User {chat_id} attempted to send a photo without selecting a role or model.')
        return

    time.sleep(1)
    bot.send_message(chat_id, 'Photo received, processing... ⏳')
    logger.info(f'User {chat_id} sent a photo.')

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open('user_photo.jpg', 'wb') as new_file:
        new_file.write(downloaded_file)

    extracted_text = extract_text_from_image('user_photo.jpg')
    user_info['user_history'].append({'role': 'user', 'content': extracted_text})
    logger.info(f'Extracted text from photo: {extracted_text}')

    response = openai.ChatCompletion.create(
        model=user_info['user_model'],
        messages=[{'role': 'system', 'content': ROLE_MESSAGES[user_info['user_role']]}, *user_info['user_history']]
    )

    bot_reply = response.choices[0].message['content']
    user_info['user_history'].append({'role': 'assistant', 'content': bot_reply})

    time.sleep(1)
    bot.reply_to(message, bot_reply)
    logger.info(f'Response to user {chat_id}: {bot_reply}')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    user_info = user_data.get(chat_id)

    if not user_info or not user_info['user_model']:
        bot.send_message(chat_id, 'Please select a role and model first.')
        logger.warning(f'User {chat_id} attempted to send a message without selecting a role or model.')
        return

    time.sleep(1)
    bot.send_message(chat_id, 'Message received, processing... ⏳')
    logger.info(f'User {chat_id} sent a message: {message.text}')
    user_info['user_history'].append({'role': 'user', 'content': message.text})

    response = openai.ChatCompletion.create(
        model=user_info['user_model'],
        messages=[{'role': 'system', 'content': ROLE_MESSAGES[user_info['user_role']]}, *user_info['user_history']]
    )

    bot_reply = response.choices[0].message['content']
    user_info['user_history'].append({'role': 'assistant', 'content': bot_reply})

    time.sleep(1)
    bot.reply_to(message, bot_reply)
    logger.info(f'Response to user {chat_id}: {bot_reply}')

bot.polling(none_stop=True)
