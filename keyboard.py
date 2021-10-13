from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import ReplyKeyboardRemove


remove_keyboard = ReplyKeyboardRemove()


start_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton('✅ Создать ПАРУ каналов ✅')
        ],
        [
            KeyboardButton('❕ Старт слова'),
            KeyboardButton('❗️ Стоп слова')
        ],
        [
            KeyboardButton('📋 Время работы')
        ],
        [
            KeyboardButton('❌ Удалить ПАРУ каналов ❌')
        ]
    ]
)

whitelist_words_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton('❗️ Отмена ❗️')
        ],
        [
            KeyboardButton('❌ Очистить список Старт слов ❌')
        ]
    ]
)

blacklist_words_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton('❗️ Отмена ❗️')
        ],
        [
            KeyboardButton('❌ Очистить список Стоп слов ❌')
        ]
    ]
)


cancal_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton('❗️ Отмена ❗️')
        ]
    ]
)
