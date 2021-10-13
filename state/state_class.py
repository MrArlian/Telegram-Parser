from aiogram.dispatcher.filters.state import State, StatesGroup


class user_state(StatesGroup):

    set_whitelist = State()
    set_blacklist = State()

    input_work_time = State()

    choose_channel_out = State()
    choose_channel_in = State()

    choose_channel_pair_delete = State()
