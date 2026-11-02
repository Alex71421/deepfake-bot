import asyncio
from bot.settings import BOT_TOKEN, ALLOWED_USER_IDS

from aiogram import Router, Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()
router.message.filter(F.from_user.id.in_(ALLOWED_USER_IDS))


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(f"Привет, {message.from_user.first_name}")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())