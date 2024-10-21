from telebot import types


def search():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Поиск канала", "Категории")
    return markup

def back_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Back", "Поиск канала")
    return markup