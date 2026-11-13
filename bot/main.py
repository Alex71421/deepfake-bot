import asyncio
from asyncio import Queue

from aiogram import Bot, Dispatcher, F

from bot.jobs import clean_jobs_dir
from bot.queue_manager import process_queue
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

    queue = Queue()
    worker_task = asyncio.create_task(process_queue(bot, queue))

    try:
        await dp.start_polling(bot, queue=queue)
    finally:
        try:
            worker_task.cancel()
            await worker_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    clean_jobs_dir()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")
