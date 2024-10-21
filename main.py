import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re, os, requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from keyboard import search, back_keyboard

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)
URLTOKEN = ""
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
        bot.send_message(
            message.chat.id,
            "Введи слово для поиска:",
            reply_markup=back_keyboard(),
        )
        bot.register_next_step_handler(message, search_channel)
    elif message.text == "Категории":
        result_dict = fetch_categories()
        global PAGES
        PAGES = form_keyboard(result_dict)
        send_menu(message.chat.id, 0)
    else:
        bot.send_message(message.chat.id, "🧾Hello! You can find tg channels", reply_markup=search())
        
def search_channel(message):
    if message.text == "Back":
        bot.send_message(message.chat.id, "🧾Hello! You can find tg channels", reply_markup=search())
    elif message.text == "Поиск канала":
        bot.send_message(
            message.chat.id,
            "Введи слово для поиска:",
            reply_markup=back_keyboard(),
        )
        bot.register_next_step_handler(message, search_channel)
    else:
        bot.send_message(message.chat.id, "⌛Collecting info...")
        global PAGES
        result_dict = process_query(query=message.text)
        PAGES = form_keyboard(result_dict)
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
        if i == 0 and len(pages) == 1:
            # First page, only "next" and "remove menu"
            navigation_buttons = []
        elif i == 0:
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

def get_token():
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en;q=0.9',
        'priority': 'u=0, i',
        'upgrade-insecure-requests': '1',
    }

    response = requests.get('https://tlgrm.ru/channels/blogs', headers=headers)
    return re.findall(r"typesense_api_key\"\:\"(.*?)\"", response.text)[0]

def get_channels(token: str, query: str, page: str = "1", per_page: str = "8"):
    headers = {
        'accept': '*/*',
        'accept-language': 'ru,en;q=0.9',
        'origin': 'https://tlgrm.ru',
        'priority': 'u=1, i',
        'referer': 'https://tlgrm.ru/',
        'x-typesense-api-key': token,
    }

    params = {
        'q': query,
        'query_by': 'name,tags,link',
        'per_page': per_page,
        'page': page,
        'query_by_weights': '120,120,10',
        'sort_by': '_eval(official:true):desc,subscribers:desc,_text_match:desc',
        'filter_by': 'lang:[na,ru]',
        'highlight_fields': '_',
        'min_len_1typo': '5',
        'min_len_2typo': '8',
    }

    response = requests.get('https://typesense.tlgrm.app/collections/channels/documents/search', params=params, headers=headers)
    return response.json()


def process_query(query: str):
    token = get_token()
    per_page = 8

    # Fetch first page and calculate total pages
    list_chan = get_channels(token=token, query=query, per_page=per_page)
    all_pages = list_chan["hits"]
    total_pages = round(list_chan["found"] / per_page)

    # Fetch remaining pages if applicable
    for page in range(2, total_pages + 1):
        all_pages += get_channels(token=token, query=query, page=str(page), per_page=per_page)["hits"]

    # Create the result dictionary
    return {f'{i["document"]["name"]} || {i["document"]["subscribers"]}': f'https://t.me/{i["document"]["link"]}' for i in all_pages}


bot.polling()
