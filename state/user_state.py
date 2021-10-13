from aiogram.dispatcher.storage import FSMContext
from aiogram.types import Message, ParseMode

from main import dispatcher

from random import randint
from datetime import time

from .state_class import user_state

from keyboard import *
from text import *

import database as db

import re


PARSE_MODE = ParseMode.HTML


@dispatcher.message_handler(state=user_state.set_whitelist)
async def set_whitelist(message: Message, state: FSMContext):

    text = message.text.lower()
    user_id = message.chat.id

    whitelist_base = db.get('users', 'whitelist', {'user_id': user_id})[0]


    if text == '❗️ отмена ❗️':
        await message.answer(cancel_action, reply_markup=start_keyboard)
        return await state.finish()


    if text == '❌ очистить список старт слов ❌':
        db.update('users', {'whitelist': '{}'}, {'user_id': user_id})

    else:
        whitelist_base.append(text)
        _tmp = '{%s}' % ','.join(whitelist_base)

        db.update('users', {'whitelist': _tmp}, {'user_id': user_id})


    user_base = db.get('users', ['whitelist', 'blacklist'], {'user_id': user_id})
    whitelist = ', '.join(user_base[0] or ['delNot'])
    blacklist = ', '.join(user_base[1] or ['delNot'])

    await message.answer(
        text=start_message % (whitelist, blacklist),
        parse_mode=PARSE_MODE,
        reply_markup=start_keyboard
    )

    await state.finish()


@dispatcher.message_handler(state=user_state.set_blacklist)
async def set_blacklist(message: Message, state: FSMContext):

    text = message.text.lower()
    user_id = message.chat.id

    blacklist_base = db.get('users', 'blacklist', {'user_id': user_id})[0]


    if text == '❗️ отмена ❗️':
        await message.answer(cancel_action, reply_markup=start_keyboard)
        return await state.finish()


    if text == '❌ очистить список стоп слов ❌':
        db.update('users', {'blacklist': '{}'}, {'user_id': user_id})

    else:
        blacklist_base.append(text)
        _tmp = '{%s}' % ','.join(blacklist_base)

        db.update('users', {'blacklist': _tmp}, {'user_id': user_id})


    user_base = db.get('users', ['whitelist', 'blacklist'], {'user_id': user_id})
    whitelist = ', '.join(user_base[0] or ['delNot'])
    blacklist = ', '.join(user_base[1] or ['delNot'])

    await message.answer(
        text=start_message % (whitelist, blacklist),
        parse_mode=PARSE_MODE,
        reply_markup=start_keyboard
    )

    await state.finish()


@dispatcher.message_handler(state=user_state.choose_channel_in)
async def choose_channel_in(message: Message, state: FSMContext):

    text = message.text.lower()

    data = await state.get_data()
    channels_input = data.get('channels_input')
    channels_output = data.get('channels_output')


    if text == '❗️ отмена ❗️':
        await message.answer(cancel_action, reply_markup=start_keyboard)
        return await state.finish()


    for channel_id, channel_name in channels_input:
        if channel_name.lower() == text:
            channel_input = [channel_id, channel_name]
            break

    channels_name = [info[1] for info in channels_output]

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton('❗️ Отмена ❗️'))
    markup.add(*channels_name)

    await message.answer(choose_channel_output, reply_markup=markup)
    await state.update_data(save=channel_input)
    await user_state.choose_channel_out.set()


@dispatcher.message_handler(state=user_state.choose_channel_out)
async def choose_channel_out(message: Message, state: FSMContext):

    text = message.text.lower()
    user_id = message.chat.id

    data = await state.get_data()
    channels_output = data.get('channels_output')
    channel_input = data.get('save')


    if text == '❗️ отмена ❗️':
        await message.answer(cancel_action, reply_markup=start_keyboard)
        return await state.finish()


    for channel_id, channel_name in channels_output:
        if channel_name.lower() == text:
            channel_output = [channel_id, channel_name]
            break

    pair_id = randint(100000, 10000000)

    db.add('channels', {
        'pair_id': pair_id,
        'user_id': user_id,
        'channel_id_input': channel_input[0],
        'channel_name_input': channel_input[1],
        'channel_id_output': channel_output[0],
        'channel_name_output': channel_output[1]
    })


    await message.answer(successfully_created, reply_markup=start_keyboard)
    await state.finish()


@dispatcher.message_handler(state=user_state.choose_channel_pair_delete)
async def choose_channel_pair_delete(message: Message, state: FSMContext):

    text = message.text.lower()

    data = await state.get_data()
    channel_data = data.get('channel_data')


    if text == '❗️ отмена ❗️':
        await message.answer(cancel_action, reply_markup=start_keyboard)
        return await state.finish()


    if text in channel_data.keys():
        pair_id = channel_data.get(text)

        db.delete('channels', {'pair_id': pair_id})

        await message.answer(successfully_deleted, reply_markup=start_keyboard)
        await state.finish()


@dispatcher.message_handler(state=user_state.input_work_time)
async def input_work_time(message: Message, state: FSMContext):

    text = message.text.lower()
    user_id = message.chat.id


    if text == '❗️ отмена ❗️':
        await message.answer(cancel_action, reply_markup=start_keyboard)
        return await state.finish()


    try:
        obj_src_1, obj_src_2 = text.split(' - ')
    except ValueError:
        return await message.answer(err_time)

    time_1 = re.findall(r'^([\d]|[0-1][\d]|[2][0-3]):([\d]|[0-5][\d]):([\d]|[0-5][\d])$', obj_src_1)
    time_2 = re.findall(r'^([\d]|[0-1][\d]|[2][0-3]):([\d]|[0-5][\d]):([\d]|[0-5][\d])$', obj_src_2)


    if time_1 and time_2:
        time_1 = str(time(*map(int, *time_1)))
        time_2 = str(time(*map(int, *time_2)))

        db.update('users', {'online': time_1, 'offline': time_2}, {'user_id': user_id})

        await message.answer(successfully_update, reply_markup=start_keyboard)
        await state.finish()

    else:
        await message.answer(err_time)
