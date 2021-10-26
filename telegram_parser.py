from telethon import TelegramClient, events, Button
from telethon.events.common import EventCommon

from telethon.tl.types import (
    DocumentAttributeFilename as AttributeFilename,
    MessageMediaDocument,
    MessageMediaGeoLive,
    MessageMediaWebPage,
    MessageMediaPhoto,
    MessageMediaDice,
    MessageMediaPoll,
    MessageMediaGeo,
    InputDocument,
    InputPhoto,
    Channel
)

from typing import Any, Tuple, Union
from configobj import ConfigObj
from ast import literal_eval
from random import randint
from json import dumps
from io import BytesIO

from modules import get_channels_id, check_time
from text import control_message

import database as db

import re
import os


cfg = ConfigObj('static/config.cfg')

API_HASH = cfg.get('API_HASH')
API_ID = cfg.get('API_ID')
PHONE = cfg.get('PHONE')
TOKEN = cfg.get('TOKEN')

UPDATES = {}

SESSION_USER = 'sessions/user_v1'
SESSION_BOT = 'sessions/bot_v1'


if 'user_v1.session-journal' in os.listdir('sessions'):
    SESSION_USER = 'sessions/user_v2'
elif 'user_v2.session-journal' in os.listdir('sessions'):
    SESSION_USER = 'sessions/user_v1'

if 'bot_v1.session-journal' in os.listdir('sessions'):
    SESSION_BOT = 'sessions/bot_v2'
elif 'bot_v2.session-journal' in os.listdir('sessions'):
    SESSION_BOT = 'sessions/bot_v1'


client = TelegramClient(SESSION_USER, API_ID, API_HASH).start(phone=PHONE)
bot = TelegramClient(SESSION_BOT, API_ID, API_HASH).start(bot_token=TOKEN)


async def get_channel() -> Tuple[list, list]:

    channels_input, channels_output = [], []

    dialog = await client.get_dialogs()


    for info in dialog:
        dialog_info = info.entity

        if isinstance(dialog_info, Channel):
            is_admin = dialog_info.admin_rights
            channel_name = dialog_info.title
            channel_id = dialog_info.id

            if is_admin is not None:
                channels_output.append([channel_id, channel_name])
            else:
                channels_input.append([channel_id, channel_name])

    return channels_input, channels_output


@client.on(events.Album(get_channels_id(), func=check_time))
async def Album(event: EventCommon):

    chat_id_input = -event.chat_id - 1000000000000
    messages = event.messages
    count = len(event)
    text = event.text

    UPDATES.update({chat_id_input: count})

    chat_ids = db.get('channels', 'channel_id_output', {'channel_id_input': chat_id_input})

    list_media = [message.media for message in messages]

    for chat_id in chat_ids:
        await _send_message(chat_id, list_media, text)


@client.on(events.NewMessage(get_channels_id(), func=check_time))
async def NewMessage(event: EventCommon):

    chat_id_input = -event.chat_id - 1000000000000
    media = event.message.media
    text = event.message.text

    if isinstance(media, MessageMediaPoll): return
    if isinstance(media, MessageMediaGeo): return
    if isinstance(media, MessageMediaDice): return
    if isinstance(media, MessageMediaGeoLive): return
    if isinstance(media, MessageMediaWebPage):
        media = None

    media = [media] if media else []

    chat_ids = db.get('channels', 'channel_id_output', {'channel_id_input': chat_id_input})

    if chat_id_input in UPDATES.keys():
        count = UPDATES.get(chat_id_input)

        if count == 1:
            UPDATES.pop(chat_id_input)
        else:
            UPDATES.update({chat_id_input: count - 1})

        raise events.StopPropagation()

    for chat_id in chat_ids:
        await _send_message(chat_id, media, text)


async def SendMessage(chat_id: int, payload: dict):

    type_send = payload.get('type')
    content = payload.get('items')
    text = payload.get('text')

    if type_send == 'message':
        await client.send_message(chat_id, text)

    elif type_send == 'media':
        media_list = []

        for type_media, server_id, server_hash, bytes_string in content:
            file_reference = literal_eval(f"b'{bytes_string[1:]}'")

            if type_media == 'photo':
                media_list.append(InputPhoto(server_id, server_hash, file_reference))
            elif type_media == 'document':
                media_list.append(InputDocument(server_id, server_hash, file_reference))

        if len(media_list) > 1:
            await client.send_file(chat_id, media_list, caption=text, video_note=True)
        else:
            await client.send_file(chat_id, media_list[0], caption=text, video_note=True)


async def _send_message(chat_id: int, media: Union[Any, list], text: str) -> None:

    user_id = db.get('channels', 'user_id', {'channel_id_output': chat_id})[0]

    user_base = db.get('users', ['blacklist', 'whitelist', 'control'], {'user_id': user_id})
    blacklist, whitelist, control = user_base

    chat_id = -chat_id - 1000000000000

    text = re.sub(r'@\S+', '@Oplata_signals_bot', text)
    object_id = randint(10000, 10000000)
    media_list, items = [], []

    black_words = bool([True for i in blacklist if i.lower() in text.lower()])
    white_words = bool([True for i in whitelist if i.lower() in text.lower()])

    if black_words is True and blacklist:
        return
    if white_words is False and whitelist:
        return
    if len(text) < 9 and not media:
        return


    markup = bot.build_reply_markup([
        [
            Button.inline('✅ Отправить', data=f'confirm-{object_id}'),
            Button.inline('🚫 Удалить', data=f'reject-{object_id}')
        ]
    ])


    if not media:

        if control is False:
            await client.send_message(chat_id, text)
        elif control is True:
            await bot.send_message(user_id, text)
            await bot.send_message(user_id, control_message, buttons=markup)

            payload = dumps(dict(type='message', text=text))

            db.add('waiting', {
                'chat_id': chat_id, 'user_id': user_id,
                'payload': payload, 'id': object_id
            })

    else:

        if control is False:
            if len(media) > 1:
                await client.send_file(chat_id, media, caption=text, video_note=True)
            else:
                await client.send_file(chat_id, media[0], caption=text, video_note=True)

        elif control is True:

            for content in media:
                _bytes = await client.download_file(content, bytes)
                file = BytesIO(_bytes)
                file_name = None

                if isinstance(content, MessageMediaDocument):
                    data = content.document

                    attributes = data.attributes
                    mime_type = data.mime_type

                    attributes.sort(key=lambda a: isinstance(a, AttributeFilename))

                    if isinstance(attributes[-1], AttributeFilename):
                        file_name = attributes[-1].file_name
                    else:
                        file_name = mime_type.replace('/', '.')

                    items.append(['document', data.id, data.access_hash, str(data.file_reference)])


                elif isinstance(content, MessageMediaPhoto):
                    items.append([
                        'photo', content.photo.id, content.photo.access_hash,
                        str(content.photo.file_reference)
                    ])


                input_file = await bot.upload_file(file, file_name=file_name)

                if len(media) > 1:
                    media_list.append(input_file)


            await bot.send_file(user_id, media_list or input_file, caption=text, video_note=True)
            await bot.send_message(user_id, control_message, buttons=markup)


            payload = dumps(dict(type='media', text=text, items=items))

            db.add('waiting', {
                'chat_id': chat_id, 'user_id': user_id,
                'payload': payload, 'id': object_id
            })


if __name__ == '__main__':
    client.run_until_disconnected()
