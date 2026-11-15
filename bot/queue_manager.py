import asyncio
import logging
import shutil
import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramNetworkError
from aiogram.types import BufferedInputFile


from bot.jobs import Job, create_job_dir, download_inputs, OUTPUT_FILENAME
from bot.notifications import update_message_text
from worker.swap import run_facefusion

FILE_UPLOAD_TIMEOUT = 10 * 60
UPDATE_PERCENT_TIME = 3
logger = logging.getLogger(__name__)


async def process_queue(bot: Bot, queue: asyncio.Queue) -> None:
    """Обрабатывает очередь и последовательное выполнение запросов"""
    while True:
        job = await queue.get()

        try:
            await process_job(bot, job)
        except Exception as e:
            logger.exception("Непредвиденная ошибка при обработке задания")
        finally:
            queue.task_done()


async def process_job(bot: Bot, job: Job) -> None:
    """Управляет процессом от взятия задачи в работу до выдачи результата"""
    logger.info("Задание взято из очереди")
    new_job_path = create_job_dir()

    try:
        try:
            message = await bot.send_message(job.chat_id, "Скачиваю файлы...")
            job.message_id = message.message_id
        except TelegramAPIError as e:
            logger.error("Не удалось отправить сообщение о загрузке файлов : %s", str(e))
            return

        try:
            source_path, video_path = await download_inputs(bot, new_job_path, job.photo_file_id,
                                                            job.video_file_id)
        except (TelegramAPIError, TimeoutError) as e:
            await update_message_text(bot, job.chat_id, job.message_id,
                                      "Не удалось скачать файлы. Попробуй ещё раз: /new")
            logger.error("Не удалось скачать файлы : %s",  str(e))
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
            logger.error("Процесс обработки видео завершился с ошибкой : %s",  str(e))
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
            logger.error("Телеграм отказал в отправке видео : %s", str(e))
            await update_message_text(bot, job.chat_id, job.message_id, "Telegram отказал в отправке видео")
            return
        except TelegramNetworkError as e:
            logger.error("Отправка видео не уложилась в срок Telegram : %s", str(e))
            await update_message_text(bot, job.chat_id, job.message_id, "Отправка не подтверждена. Видео еще может прийти")
            return
        except TelegramAPIError as e:
            logger.error("Не удалось отправить видео : %s", str(e))
            await update_message_text(bot, job.chat_id, job.message_id, "Не удалось отправить результат")
            return

        logger.info("Видео успешно отправлено пользователю")
        await update_message_text(bot, job.chat_id, job.message_id, "Готово!")

    finally:
        shutil.rmtree(new_job_path, ignore_errors=True)