from telethon.sessions import StringSession
from telethon import TelegramClient

from telethon.tl.types import (
    InputDocument,
    InputPhoto,
    Channel
)

from configobj import ConfigObj
from ast import literal_eval
from typing import Tuple


cfg = ConfigObj('static/config.cfg')

SECRET_TOKENS = cfg.get('SECRET_TOKENS')
API_HASH = cfg.get('API_HASH')
API_ID = cfg.get('API_ID')

USER = literal_eval(SECRET_TOKENS).get('user')


client = TelegramClient(StringSession(USER), API_ID, API_HASH)


async def get_channels() -> Tuple[list, list]:

    await client.connect()

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


async def SendMessage(chat_id: int, text: str, content: list, object_type: str) -> None:

    await client.connect()

    if object_type == 'message':
        await client.send_message(chat_id, text)

    elif object_type == 'media':
        media_list = []

        for content_type, server_id, server_hash, bytes_string in content:
            file_reference = literal_eval(f"b'{bytes_string[1:]}'")

            if content_type == 'photo':
                media_list.append(InputPhoto(server_id, server_hash, file_reference))
            elif content_type == 'document':
                media_list.append(InputDocument(server_id, server_hash, file_reference))

        if len(media_list) > 1:
            await client.send_file(chat_id, media_list, caption=text, video_note=True)
        else:
            await client.send_file(chat_id, media_list[0], caption=text, video_note=True)
