import asyncio
import shutil
import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramNetworkError
from aiogram.types import BufferedInputFile

from bot.handlers.swap import update_message_text
from bot.jobs import Job, create_job_dir, download_inputs, OUTPUT_FILENAME
from worker.swap import run_facefusion

FILE_UPLOAD_TIMEOUT = 10 * 60
UPDATE_PERCENT_TIME = 3


async def process_queue(bot: Bot, queue: asyncio.Queue) -> None:
    """Обрабатывает очередь и последовательное выполнение запросов"""
    while True:
        job = await queue.get()

        try:
            await process_job(bot, job)
        except Exception as e:
            print(type(e).__name__, str(e))
        finally:
            queue.task_done()


async def process_job(bot: Bot, job: Job) -> None:
    new_job_path = create_job_dir()

    try:
        await update_message_text(bot, job.chat_id, job.message_id, "Скачиваю файлы...")
        try:
            source_path, video_path = await download_inputs(bot, new_job_path, job.photo_file_id,
                                                            job.video_file_id)
        except (TelegramAPIError, TimeoutError) as e:
            await update_message_text(bot, job.chat_id, job.message_id,
                                      "Не удалось скачать файлы. Попробуй ещё раз: /new")
            print(e)
            return

        output_path = new_job_path / OUTPUT_FILENAME
        await update_message_text(bot, job.chat_id, job.message_id,
                                  "Обрабатываю видео, это займёт пару минут...")

        last_update = 0

        async def update_progress(stage: str, percent: int) -> None:
            """Редактирует сообщение относительно прогресса генерации"""
            nonlocal last_update
            if stage != "processing":
                return
            if time.monotonic() - last_update < UPDATE_PERCENT_TIME:
                return
            last_update = time.monotonic()
            await update_message_text(bot, job.chat_id, job.message_id,
                                      f"Обрабатываю видео: {percent}%")

        try:
            await run_facefusion(source_path, video_path, output_path, face_selector_mode=job.mode,
                                 on_progress=update_progress)
        except (FileNotFoundError, RuntimeError) as e:
            print(e)
            await update_message_text(bot, job.chat_id, job.message_id,
                                      "Не удалось обработать видео. Попробуй ещё раз: /new")
            return

        await update_message_text(bot, job.chat_id, job.message_id,"Отправляю видео в чат...")

        try:
            await bot.send_video(
                job.chat_id,
                BufferedInputFile(output_path.read_bytes(), filename="result.mp4"),
                request_timeout=FILE_UPLOAD_TIMEOUT,
            )
        except TelegramBadRequest as e:
            print(type(e).__name__, str(e))
            await update_message_text(bot, job.chat_id, job.message_id, "Telegram отказал в отправке видео")
            return
        except TelegramNetworkError as e:
            print(type(e).__name__, str(e))
            await update_message_text(bot, job.chat_id, job.message_id, "Отправка не подтверждена. Видео еще может прийти")
            return
        except TelegramAPIError as e:
            print(type(e).__name__, str(e))
            await update_message_text(bot, job.chat_id, job.message_id, "Не удалось отправить результат")
            return

        await update_message_text(bot, job.chat_id, job.message_id, "Готово!")

    finally:
        shutil.rmtree(new_job_path, ignore_errors=True)