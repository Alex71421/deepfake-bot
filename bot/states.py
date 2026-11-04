from aiogram.fsm.state import StatesGroup, State


class SwapForm(StatesGroup):
    waiting_face = State()
    waiting_video = State()
    waiting_mode = State()
    waiting_confirm = State()