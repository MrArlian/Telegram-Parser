from telethon.events.common import EventCommon

from datetime import datetime
from pytz import timezone

import database as db


def get_channels_id() -> list:
    return db.get('channels', 'channel_id_input')


def check_time(event: EventCommon) -> bool:

    chat_id = -event.chat_id - 1000000000000

    user_id = db.get('channels', 'user_id', {'channel_id_input': chat_id})[0]
    user_base = db.get('users', ['online', 'offline'], {'user_id': user_id})
    online, offline = user_base

    tz = timezone('Europe/Simferopol')
    now_time = datetime.now(tz).time()

    return online <= now_time <= offline
