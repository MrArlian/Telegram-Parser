from telethon.events.common import EventCommon
from telethon import TelegramClient, events
from telethon.tl.types import Channel

from configobj import ConfigObj
from datetime import datetime
from pytz import timezone
from typing import Tuple

import database as db

import re


cfg = ConfigObj('static/config.cfg')

API_HASH = cfg.get('API_HASH')
API_ID = cfg.get('API_ID')
PHONE = cfg.get('PHONE')

TZ = timezone('Europe/Simferopol')


client = TelegramClient('user', API_ID, API_HASH).start(phone=PHONE)


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


def get_channels_id() -> list:
    return db.get('channels', 'channel_id_input')


def check_time(event: EventCommon) -> bool:

    chat_id = -event.chat_id - 1000000000000

    user_id = db.get('channels', 'user_id', {'channel_id_input': chat_id})[0]
    user_base = db.get('users', ['online', 'offline'], {'user_id': user_id})
    online, offline = user_base

    now = datetime.now(TZ)
    now_time = now.time()

    return online <= now_time <= offline


@client.on(events.NewMessage(get_channels_id(), incoming=False, func=check_time))
async def NewMessage(event: EventCommon):

    chat_id_input = -event.chat_id - 1000000000000
    media = event.message.media
    text = event.message.text

    channel_info = db.get(
        table='channels',
        objects=['user_id', 'channel_id_output'],
        condition={'channel_id_input': chat_id_input}
    )

    user_id, chat_id_output = channel_info

    user_base = db.get('users', ['whitelist', 'blacklist'], {'user_id': user_id})
    whitelist, blacklist = user_base


    text = re.sub(r'@\S+', '@my_nickname', text)

    obj_1 = bool([True for i in whitelist if i in text])
    obj_2 = bool([True for i in blacklist if i in text])

    if not whitelist and not blacklist:
        obj_1, obj_2 = True, False

    if media is None and obj_1 and not obj_2 and len(text) > 0:
        await client.send_message(chat_id_output, text)

    elif media is not None:
        await client.send_file(chat_id_output, media, caption=text)


if __name__ == '__main__':
    client.run_until_disconnected()
