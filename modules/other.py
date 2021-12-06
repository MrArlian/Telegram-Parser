from telethon.events.common import EventCommon
from telethon.utils import get_peer_id

from datetime import datetime
from pytz import timezone

import database as db


TZ = timezone('Europe/Simferopol')


def get_channels_id() -> list:
    return db.get('channels', 'channel_id_input')


def check_time(event: EventCommon) -> bool:

    chat_id = get_peer_id(event.chat_id, False)

    user_id = db.get('channels', 'user_id', {'channel_id_input': chat_id})[0]
    base = db.get('users', ['online', 'offline'], {'user_id': user_id})
    online, offline = base

    now_time = datetime.now(TZ).time()

    return online <= now_time <= offline
