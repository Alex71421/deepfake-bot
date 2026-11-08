import shutil
import uuid
from pathlib import Path
from shutil import rmtree

from aiogram import Bot

from bot.settings import JOBS_DIR


SOURCE_FILENAME = "source.jpg"
TARGET_FILENAME = "target.mp4"
OUTPUT_FILENAME = "result.mp4"


def create_job_dir() -> Path:
    """Создает папку для дипфейка со случайным названием"""
    directory_name = uuid.uuid4().hex
    path = JOBS_DIR / directory_name
    path.mkdir(parents=True, exist_ok=True)
    return path


async def download_inputs(bot: Bot, job_path: Path, photo_file_id: str, video_file_id: str) -> tuple[Path, Path]:
    """Скачивает фото и видео и помещает в указанную папку"""
    photo_path = job_path / SOURCE_FILENAME
    video_path = job_path / TARGET_FILENAME
    await bot.download(photo_file_id, destination=photo_path)
    await bot.download(video_file_id, destination=video_path)
    return photo_path, video_path


def clean_jobs_dir() -> None:
    """Удаляет все папки задач, оставшиеся от прошлых запусков"""
    if not JOBS_DIR.is_dir():
        return
    delete_count = 0
    for job_dir in JOBS_DIR.iterdir():
        if job_dir.is_dir():
            shutil.rmtree(job_dir, ignore_errors=True)
            delete_count += 1
    print(f"Удалено ненужных папок: {delete_count}")