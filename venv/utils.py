from telebot import types
from PIL import Image
import pytesseract
import time
from constants import TESSERACT_PATH, ROLE_IMAGES
from messages import WELCOME_MESSAGE, ROLE_MESSAGES, ROLE_SELECTED_MESSAGE, MODEL_SELECTED_MESSAGES

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def start_command(bot, message, user_data, logger):
    user_data[message.chat.id] = {'user_model': '', 'user_role': '', 'user_history': []}
    bot.send_message(message.chat.id, WELCOME_MESSAGE, reply_markup=create_role_buttons())
    logger.info(f'User {message.chat.id} started the bot.')

def create_role_buttons():
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton('Learn languages 🇬🇧', callback_data='language_learning'),
        types.InlineKeyboardButton('Study programming 👨‍💻', callback_data='programming_helper'),
        types.InlineKeyboardButton('Share thoughts and feelings 🤗', callback_data='psychologist'),
        types.InlineKeyboardButton('Write an essay ✍️', callback_data='essay_writer')
    ]
    markup.add(*buttons)
    return markup

def send_role_image(bot, chat_id, role):
    with open(ROLE_IMAGES[role], 'rb') as photo:
        bot.send_photo(chat_id, photo)

def create_model_buttons():
    markup = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton('GPT-3.5 Turbo', callback_data='gpt-3.5-turbo'),
        types.InlineKeyboardButton('GPT-4', callback_data='gpt-4'),
        types.InlineKeyboardButton('GPT-4 Turbo', callback_data='gpt-4-turbo')
    ]
    markup.add(*buttons)
    return markup

def handle_selection(bot, call, user_data, logger):
    chat_id = call.message.chat.id
    user_info = user_data.get(chat_id)

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    bot.delete_message(chat_id, call.message.message_id)

    if call.data in ['language_learning', 'programming_helper', 'psychologist', 'essay_writer']:
        user_info['user_role'] = call.data
        logger.info(f'User {chat_id} selected role: {call.data}')

        # Отправка сообщения о выбранной роли
        time.sleep(1)
        role_message_text = ROLE_MESSAGES.get(call.data, 'Role not found.')
        bot.send_message(chat_id, role_message_text)
        send_role_image(bot, chat_id, call.data)

        time.sleep(1)
        role_message = bot.send_message(chat_id, ROLE_SELECTED_MESSAGE, reply_markup=create_model_buttons())
        user_info['role_message_id'] = role_message.message_id

    elif call.data in ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']:
        user_info['user_model'] = call.data
        logger.info(f'User {chat_id} selected model: {call.data}')

        # Отправка сообщения о выбранной модели
        time.sleep(1)
        model_message_text = MODEL_SELECTED_MESSAGES.get(call.data, 'Model not found.')
        bot.send_message(chat_id, model_message_text)



def handle_photo(bot, message, user_data, logger):
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
        messages=[{'role': 'system', 'content': f'Role: {user_info["user_role"]}'}, *user_info['user_history']]
    )

    bot_reply = response.choices[0].message['content']
    user_info['user_history'].append({'role': 'assistant', 'content': bot_reply})

    time.sleep(1)
    bot.reply_to(message, bot_reply)
    logger.info(f'Response to user {chat_id}: {bot_reply}')


def handle_text(bot, message, user_data, logger):
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
        messages=[{'role': 'system', 'content': f'Role: {user_info["user_role"]}'}, *user_info['user_history']]
    )

    bot_reply = response.choices[0].message['content']
    user_info['user_history'].append({'role': 'assistant', 'content': bot_reply})

    time.sleep(1)
    bot.reply_to(message, bot_reply)
    logger.info(f'Response to user {chat_id}: {bot_reply}')
