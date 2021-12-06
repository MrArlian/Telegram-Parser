from telethon.events.common import EventBuilder, EventCommon, name_inner_event
from telethon.tl.types import UpdateNewChannelMessage, PeerUser


SKIP_UPDATES = set()


@name_inner_event
class NewEvent(EventBuilder):

    def __init__(self, chats=None, *, func=None):
        super().__init__(chats=chats, func=func)


    @classmethod
    def build(cls, update, others=None, self_id=None):

        if not others: return

        _ev_id = id(update)


        if isinstance(update, UpdateNewChannelMessage):

            if _ev_id in SKIP_UPDATES:
                SKIP_UPDATES.remove(_ev_id)
                return

            for up in others:
                if isinstance(up, UpdateNewChannelMessage) and up is not update:
                    SKIP_UPDATES.add(id(up))

            return cls.Event([
                up for up in others
                    if isinstance(up, UpdateNewChannelMessage)
            ])


    class Event(EventCommon):

        def __init__(self, messages: list) -> None:
            message = messages[0].message

            if isinstance(message.peer_id, PeerUser):
                chat = message.from_id
            else:
                chat = message.peer_id

            super().__init__(chat_peer=chat,
                             msg_id=message.id,
                             broadcast=bool(message.post))

            self.messages = messages


        @property
        def text(self) -> str:
            return next((m.message.message for m in self.messages if m.message.message), '')

        @property
        def media(self) -> list:
            return [m.message.media for m in self.messages if m.message.media]
