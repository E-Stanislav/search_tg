import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re, os, requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from telebot import types

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Define static pages
PAGES = [
    [[InlineKeyboardButton("Коридор", url="https://example.com/corridor")], [InlineKeyboardButton("➡️ Вперёд", callback_data='next_page')]],
    [[InlineKeyboardButton("Спальня", url="https://example.com/bedroom")], [InlineKeyboardButton("⬅️ Назад", callback_data='prev_page')], [InlineKeyboardButton("➡️ Вперёд", callback_data='next_page')]],
    [[InlineKeyboardButton("Видеозвонок", url="https://example.com/video_call")], [InlineKeyboardButton("❌ Убрать меню", callback_data='remove_menu')], [InlineKeyboardButton("⬅️ Назад", callback_data='prev_page')]]
]

def generate_header(page_index, total_pages):
    return f"🔧 Выбрать страницу (Стр. {page_index + 1} из {total_pages}):" if total_pages > 1 else "🔧 Выбрать страницу:"

def send_menu(chat_id, page_index, message_id=None):
    total_pages = len(PAGES)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(*[btn for row in PAGES[page_index] for btn in row])
    header = generate_header(page_index, total_pages)
    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=header, reply_markup=markup)
    else:
        bot.send_message(chat_id, header, reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "🧾Hello! You can find tg channels", reply_markup=search())

@bot.message_handler(content_types="text")
def main(message):
    if message.text == "Поиск канала":
        bot.send_message(message.chat.id, "🧾Hello! You can find tg channels", reply_markup=search())
    elif message.text == "Категории":
        result_dict = fetch_categories()
        global PAGES
        PAGES = form_keyboard(result_dict)
        send_menu(message.chat.id, 0)
    else:
        send_menu(message.chat.id, 0)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    current_page = int(re.findall(r"Стр\. (\d+) из", call.message.text)[0]) - 1 if "Стр." in call.message.text else 0
    if call.data == "next_page" and current_page < len(PAGES) - 1:
        send_menu(call.message.chat.id, current_page + 1, call.message.message_id)
    elif call.data == "prev_page" and current_page > 0:
        send_menu(call.message.chat.id, current_page - 1, call.message.message_id)
    elif call.data == "remove_menu":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Меню убрано.")

def search():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Поиск канала", "Категории")
    return markup

def fetch_categories():
    headers = {
        'Referer': 'https://tlgrm.ru/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36',
    }
    response = requests.get('https://tlgrm.ru/channels', headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = [i.text.strip() for i in soup.select('.channel-category__name')]
    hrefs = [a['href'] for a in soup.select('.channels-categories a[href]')][1:]
    return dict(zip(titles, hrefs))

def form_keyboard(input_dict):
    chunk_size = 6
    items = list(input_dict.items())
    pages = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
    
    result_pages = []
    
    for i, page in enumerate(pages):
        page_buttons = [[InlineKeyboardButton(name, url=link)] for name, link in page]
        
        # Add navigation buttons depending on the page's position
        if i == 0:
            # First page, only "next" and "remove menu"
            navigation_buttons = [InlineKeyboardButton("➡️ Вперёд", callback_data='next_page')]
        elif i < len(pages) - 1:
            # Inner pages, "prev", "next", and "remove menu"
            navigation_buttons = [InlineKeyboardButton("⬅️ Назад", callback_data='prev_page'), InlineKeyboardButton("➡️ Вперёд", callback_data='next_page')]
        else:
            # Last page, only "prev" and "remove menu"
            navigation_buttons = [InlineKeyboardButton("⬅️ Назад", callback_data='prev_page')]
        
        # Add the "remove menu" button
        navigation_buttons.append(InlineKeyboardButton("❌ Убрать меню", callback_data='remove_menu'))
        
        # Append the navigation buttons to the page
        result_pages.append(page_buttons + [navigation_buttons])
    
    return result_pages


bot.polling()
