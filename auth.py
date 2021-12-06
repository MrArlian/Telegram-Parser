from telethon.sessions import StringSession
from telethon import TelegramClient

from configobj import ConfigObj
from json import dumps


cfg = ConfigObj('static/config.cfg')

API_HASH = cfg.get('API_HASH')
API_ID = cfg.get('API_ID')

PHONE = cfg.get('PHONE')
TOKEN = cfg.get('TOKEN')


def main():

    #No data
    assert PHONE and TOKEN, 'Укажите номер телефона или токен бота в config файле!'
    assert API_ID and API_HASH, 'Укажите api_id и api_hash в config файле!'

    #Authorize user
    with TelegramClient(StringSession(), API_ID, API_HASH).start(phone=PHONE) as user:
        session_user = user.session.save()

    #Authorize bot
    with TelegramClient(StringSession(), API_ID, API_HASH).start(bot_token=TOKEN) as bot:
        session_bot = bot.session.save()


    _data = dumps({'user': session_user, 'bot': session_bot}, indent=4)

    cfg.update({'SECRET_TOKENS': _data})
    cfg.write()


if __name__ == '__main__':
    main()
