import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.settings import BOT_TOKEN, ALLOWED_USER_IDS

from aiogram import Router, Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()
router.message.filter(F.from_user.id.in_(ALLOWED_USER_IDS))

class SwapForm(StatesGroup):
    waiting_face = State()
    waiting_video = State()
    waiting_mode = State()
    waiting_confirm = State()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(f"Привет, {message.from_user.first_name}")


@router.message(Command("new"))
async def new_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(SwapForm.waiting_face)
    await message.answer("Пришлите фото с лицом")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())