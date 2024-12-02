from telebot import types
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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


def create_model_buttons():
    markup = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton('GPT-3.5 Turbo', callback_data='gpt-3.5-turbo'),
        types.InlineKeyboardButton('GPT-4', callback_data='gpt-4'),
        types.InlineKeyboardButton('GPT-4 Turbo', callback_data='gpt-4-turbo')
    ]
    markup.add(*buttons)
    return markup


def send_role_image(bot, chat_id, role):
    role_images = {
        'language_learning': 'lang_role.png',
        'programming_helper': 'prog_role.png',
        'psychologist': 'psy_role.jpg',
        'essay_writer': 'essays_role.png'
    }
    with open(role_images[role], 'rb') as photo:
        bot.send_photo(chat_id, photo)


def extract_text_from_image(image_path):
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)
