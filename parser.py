from telethon.events.common import EventCommon
from telethon.sessions import StringSession
from telethon import TelegramClient, Button
from telethon.utils import get_peer_id

from telethon.tl.types import (
    DocumentAttributeFilename as AttributeFilename,
    MessageMediaDocument,
    MessageMediaPhoto
)

from configobj import ConfigObj
from typing import Any, Union
from ast import literal_eval
from random import randint
from io import BytesIO
from json import dumps

from modules import NewEvent, get_channels_id, check_time
from text import control_message

import database as db

import asyncio
import re


cfg = ConfigObj('static/config.cfg')

SECRET_TOKENS = cfg.get('SECRET_TOKENS')
API_HASH = cfg.get('API_HASH')
API_ID = cfg.get('API_ID')
NAME = cfg.get('NAME')

USER = literal_eval(SECRET_TOKENS).get('user')
BOT = literal_eval(SECRET_TOKENS).get('bot')


client = TelegramClient(StringSession(USER), API_ID, API_HASH)
bot = TelegramClient(StringSession(BOT), API_ID, API_HASH)


@client.on(NewEvent(get_channels_id(), func=check_time))
async def NewMessage(event: EventCommon):

    chat_id = get_peer_id(event.chat_id, False)
    content = event.media
    text = event.text

    channels = db.get('channels', 'channel_id_output', {'channel_id_input': chat_id})

    for media in content:
        if not isinstance(media, (MessageMediaDocument, MessageMediaPhoto)):
            return

    if len(content) == 1:
        content = content[0]

    for channel in channels:
        user_id = db.get('channels', 'user_id', {'channel_id_output': channel})[0]

        user_base = db.get('users', ['blacklist', 'whitelist', 'control'], {'user_id': user_id})
        blacklist, whitelist, control = user_base

        await _send_message(channel, user_id, content, text, blacklist, whitelist, control)


async def _send_message(
    chat_id: int,
    user_id: int,
    media: Union[Any, list],
    text: str,
    blacklist: list,
    whitelist: list,
    control: bool
) -> None:

    _text_split = text.lower().split(' ')
    chat_id = -chat_id - 1000000000000

    object_id = randint(10000, 10000000)
    text = re.sub(r'@\S+', NAME, text)
    media_list, items = [], []

    buttons = [
        [
            Button.inline('✅ Отправить', data=f'confirm-{object_id}'),
            Button.inline('🚫 Удалить', data=f'reject-{object_id}')
        ]
    ]


    if not set(whitelist).intersection(_text_split) and whitelist:
        return
    if set(blacklist).intersection(_text_split):
        return

    if len(text) < 9 and not media:
        return

    if not media:

        if control is False:
            await client.send_message(chat_id, text)

        elif control is True:
            payload = dumps(dict(type='message', text=text))
            db.add('waiting', {'chat_id': chat_id, 'id': object_id, 'payload': payload})

            await bot.send_message(user_id, text)
            await bot.send_message(user_id, control_message, buttons=buttons)

    else:

        if control is False:
            await client.send_file(chat_id, media, caption=text, video_note=True)

        elif control is True:

            for content in media if isinstance(media, list) else [media]:
                _bytes = await client.download_file(content, bytes)
                file = BytesIO(_bytes)
                file_name = None

                if isinstance(content, MessageMediaDocument):
                    items.append(['document',
                                  content.document.id,
                                  content.document.access_hash,
                                  str(content.document.file_reference)])

                    if isinstance(content.document.attributes[-1], AttributeFilename):
                        file_name = content.document.attributes[-1].file_name
                    else:
                        file_name = content.document.mime_type.replace('/', '.')

                elif isinstance(content, MessageMediaPhoto):
                    items.append(['photo',
                                  content.photo.id,
                                  content.photo.access_hash,
                                  str(content.photo.file_reference)])

                input_file = await bot.upload_file(file, file_name=file_name)

                if isinstance(media, list):
                    media_list.append(input_file)

            payload = dumps(dict(type='media', text=text, items=items))
            db.add('waiting', {'chat_id': chat_id, 'id': object_id, 'payload': payload})

            await bot.send_file(user_id, media_list or input_file, caption=text, video_note=True)
            await bot.send_message(user_id, control_message, buttons=buttons)


async def _auth():
    await bot.connect()
    await client.connect()
    await client.run_until_disconnected()


if __name__ == '__main__':
    _loop = asyncio.get_event_loop()
    _loop.run_until_complete(_auth())
