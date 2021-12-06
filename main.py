from aiogram.dispatcher.storage import FSMContext
from aiogram.utils.executor import start_polling
from aiogram.dispatcher import Dispatcher
from aiogram import Bot

from aiogram.types import Message, CallbackQuery, ChatType, ParseMode
from aiogram.dispatcher.filters import CommandStart, ChatTypeFilter
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from configobj import ConfigObj

from modules import get_channels, SendMessage
from state.state_class import user_state
from keyboard import *
from text import *

import database as db


cfg = ConfigObj('static/config.cfg')

CHAT_PRIVATE = ChatType.PRIVATE
PARSE_MODE = ParseMode.HTML
TOKEN = cfg.get('TOKEN')


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)



@dispatcher.message_handler(CommandStart())
async def stating(message: Message):

    user_id = message.chat.id

    db.add('users', {'user_id': user_id}, 'user_id')

    user_base = db.get('users', ['whitelist', 'blacklist'], {'user_id': user_id})
    whitelist = ', '.join(user_base[0] or ['delNot'])
    blacklist = ', '.join(user_base[1] or ['delNot'])

    await message.answer(
        text=start_message % (whitelist, blacklist),
        parse_mode=PARSE_MODE,
        reply_markup=start_keyboard
    )


@dispatcher.message_handler(ChatTypeFilter(CHAT_PRIVATE))
async def lobby(message: Message, state: FSMContext):

    text = message.text.lower()
    user_id = message.chat.id

    channels = db.get(
        table='channels',
        objects=['pair_id', 'channel_name_input', 'channel_name_output'],
        condition={'user_id': user_id},
        compressing=False
    )

    control = db.get('users', 'control', {'user_id': user_id})[0]


    if text == '✅ создать пару каналов ✅':
        await message.answer(waiting_text, reply_markup=remove_keyboard)

        channels_input, channels_output = await get_channels()
        channels_name = [info[1] for info in channels_input]

        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(KeyboardButton('❗️ Отмена ❗️'))
        markup.add(*channels_name)

        await message.answer(choose_channel_input, reply_markup=markup)
        await user_state.choose_channel_in.set()

        await state.update_data(channels_input=channels_input, channels_output=channels_output)

    elif text == '📋 время работы':
        await message.answer(input_work_time_text, reply_markup=cancal_keyboard)
        await user_state.input_work_time.set()

    elif text == '📝 контроль сообщений' and control is True:
        await message.answer(control_message_on, reply_markup=control_off)

    elif text == '📝 контроль сообщений' and control is False:
        await message.answer(control_message_off, reply_markup=control_on)

    elif text == '✅ включить ✅':
        await message.answer(control_on_text, reply_markup=start_keyboard)
        db.update('users', {'control': True}, {'user_id': user_id})

    elif text == '❌ выключить ❌':
        await message.answer(control_off_text, reply_markup=start_keyboard)
        db.update('users', {'control': False}, {'user_id': user_id})

    elif text == '❕ старт слова':
        await message.answer(input_words, PARSE_MODE, reply_markup=whitelist_words_keyboard)
        await user_state.set_whitelist.set()

    elif text == '❗️ стоп слова':
        await message.answer(input_words, PARSE_MODE, reply_markup=blacklist_words_keyboard)
        await user_state.set_blacklist.set()

    elif text == '❌ удалить пару каналов ❌':
        _channel_data, _buttons = {}, []

        for channel_info in channels:
            channel_name = channel_info[1:]
            pair_id = channel_info[0]

            btn = ' 🔜 '.join(channel_name)

            _channel_data.update({btn.lower(): pair_id})
            _buttons.append(btn)

        _buttons.reverse()

        if channels:
            markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            markup.add(KeyboardButton('❗️ Отмена ❗️'))
            markup.add(*_buttons)

            msg = choose_channel_pair_delete_text + '\n'.join(_buttons)
            await message.answer(msg, reply_markup=markup)
            await user_state.choose_channel_pair_delete.set()

            await state.update_data(channel_data=_channel_data)

        else:
            await message.answer(empty_here_text)

    elif text == 'главное меню':
        await message.answer(back, reply_markup=start_keyboard)


@dispatcher.callback_query_handler(ChatTypeFilter(CHAT_PRIVATE))
async def inline(callback: CallbackQuery):

    command, object_id = callback.data.split('-')

    info_message = db.get('waiting', ['chat_id', 'payload'], {'id': object_id})
    chat_id, payload = info_message

    object_type = payload.get('type')
    content = payload.get('items')
    text = payload.get('text')

    db.delete('waiting', {'id': object_id})

    try:
        await callback.message.delete()
    except Exception:
        pass


    if command == 'confirm':
        await SendMessage(chat_id, text, content, object_type)
        await callback.answer(action_confirmed)

    elif command == 'reject':
        await callback.answer(action_rejected)


if __name__ == '__main__':
    from state import dp

    start_polling(dp)
