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

logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

user_data = {}

load_dotenv()


@bot.message_handler(commands=['start'])
def start_command(message):
    user_data[message.chat.id] = {'user_model': '', 'user_role': '', 'user_history': []}
    bot.send_message(message.chat.id, WELCOME_MESSAGE, reply_markup=create_role_buttons())
    logging.info(f'User {message.chat.id} started the bot.')


@bot.callback_query_handler(func=lambda call: True)
def handle_selection(call):
    chat_id = call.message.chat.id
    user_info = user_data.get(chat_id)

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    bot.delete_message(chat_id, call.message.message_id)

    if call.data in ROLE_MESSAGES:
        user_info['user_role'] = call.data
        logging.info(f' User {chat_id} selected role: {call.data}')

        time.sleep(1)
        bot.send_message(chat_id, ROLE_MESSAGES[call.data])
        send_role_image(bot, chat_id, call.data)

        time.sleep(1)
        role_message = bot.send_message(chat_id, ROLE_SELECTED_MESSAGE, reply_markup=create_model_buttons())
        user_info['role_message_id'] = role_message.message_id
    elif call.data in GPT_MODELS:
        user_info['user_model'] = call.data
        logging.info(f'User {chat_id} selected model: {call.data}')

        if 'role_message_id' in user_info:
            try:
                bot.delete_message(chat_id, user_info['role_message_id'])
            except Exception as e:
                logging.warning(f'Something bad:{e}')

        time.sleep(1)
        bot.send_message(chat_id, MODEL_SELECTED_MESSAGES[call.data])


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    user_info = user_data.get(chat_id)

    if not user_info or not user_info['user_model']:
        bot.send_message(chat_id, 'Please select a role and model first.')
        logging.warning(f'User {chat_id} The user as stupid as brick and tried to send a photo without selecting role '
                        f'or model.')
        return

    time.sleep(1)
    bot.send_message(chat_id, 'Photo received, processing... ⏳')
    logging.info(f'User {chat_id} sent a photo.')

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open('user_photo.jpg', 'wb') as new_file:
        new_file.write(downloaded_file)

    extracted_text = extract_text_from_image('user_photo.jpg')
    user_info['user_history'].append({'role': 'user', 'content': extracted_text})
    logging.info(f'From photo: {extracted_text}')

    response = openai.ChatCompletion.create(
        model=user_info['user_model'],
        messages=[{'role': 'system', 'content': ROLE_MESSAGES[user_info['user_role']]}, *user_info['user_history']]
    )

    bot_reply = response.choices[0].message['content']
    user_info['user_history'].append({'role': 'assistant', 'content': bot_reply})

    time.sleep(1)
    bot.reply_to(message, bot_reply)
    logging.info(f'User {chat_id}: {bot_reply}')


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    user_info = user_data.get(chat_id)

    if not user_info or not user_info['user_model']:
        bot.send_message(chat_id, 'Please select a role and model first.')
        logging.warning(f'User {chat_id} The user as stupid as brick and tried to send a message without selecting role'
                        f' or model.')
        return None

    time.sleep(1)
    bot.send_message(chat_id, 'The message received, processing... ⏳')
    logging.info(f'User {chat_id}: {message.text}')
    user_info['user_history'].append({'role': 'user', 'content': message.text})

    response = openai.ChatCompletion.create(
        model=user_info['user_model'],
        messages=[{'role': 'system', 'content': ROLE_MESSAGES[user_info['user_role']]}, *user_info['user_history']]
    )

    bot_reply = response.choices[0].message['content']
    user_info['user_history'].append({'role': 'assistant', 'content': bot_reply})

    time.sleep(1)
    bot.reply_to(message, bot_reply)
    logging.info(f'User {chat_id}: {bot_reply}')


bot.polling(none_stop=True)
