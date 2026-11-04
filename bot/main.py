import asyncio

from aiogram import Bot, Dispatcher, F

from bot.settings import BOT_TOKEN, ALLOWED_USER_IDS
from bot.handlers.common import router as common_router
from bot.handlers.swap import router as swap_router


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.message.filter(F.from_user.id.in_(ALLOWED_USER_IDS))
    dp.callback_query.filter(F.from_user.id.in_(ALLOWED_USER_IDS))
    dp.include_router(common_router)
    dp.include_router(swap_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
