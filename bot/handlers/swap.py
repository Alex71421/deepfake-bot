import shutil
import time

from aiogram import F, Router, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from bot.jobs import create_job_dir, download_inputs, OUTPUT_FILENAME
from bot.keyboards import build_mode_keyboard, build_confirm_keyboard, MODE_LABELS
from bot.settings import MAX_VIDEO_DURATION, MAX_VIDEO_SIZE
from bot.states import SwapForm
from worker.swap import run_facefusion

router = Router()

FILE_UPLOAD_TIMEOUT = 5 * 60
UPDATE_PERCENT_TIME = 3


@router.message(Command("new"))
async def new_handler(message: Message, state: FSMContext) -> None:
    """Начинает 1 этап создания дипфейка: ожидает приема фото"""
    await state.clear()
    await state.set_state(SwapForm.waiting_face)
    await message.answer("Пришлите фото с лицом")


@router.message(SwapForm.waiting_face, F.photo)
async def photo_handler(message: Message, state: FSMContext) -> None:
    """Принимает фото и меняет состояние на ожидание видео"""
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    await state.set_state(SwapForm.waiting_video)
    await message.answer("Фото принято, теперь пришлите видео")


@router.message(SwapForm.waiting_face)
async def wrong_photo_handler(message: Message) -> None:
    """Обрабатывает неверный тип файла: пришло не фото"""
    await message.answer("Нужно именно фото")


@router.message(SwapForm.waiting_video, F.video)
async def video_handler(message: Message, state: FSMContext) -> None:
    """Принимает видео и меняет состояние на ожидание выбора режима"""
    if message.video.file_size is None or message.video.file_size > MAX_VIDEO_SIZE:
        await message.answer(f"Размер видео превышает допустимое значение {MAX_VIDEO_SIZE // 2 ** 20}мб")
        return
    if message.video.duration is None or message.video.duration > MAX_VIDEO_DURATION:
        await message.answer(f"Длительность видео превышает допустимое значение {MAX_VIDEO_DURATION}с")
        return
    video_file_id = message.video.file_id
    await state.update_data(video_file_id=video_file_id)
    await state.set_state(SwapForm.waiting_mode)
    await message.answer("Видео принято, выберите режим наложения лиц", reply_markup=build_mode_keyboard())


@router.message(SwapForm.waiting_video)
async def wrong_video_handler(message: Message) -> None:
    """Обрабатывает неверный тип файла: пришло не видео"""
    await message.answer("Нужно именно видео")


@router.callback_query(SwapForm.waiting_mode, F.data.startswith("mode:"))
async def mode_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Принимает режим наложения лица по нажатию кнопки выбора"""
    mode = callback.data.split(":")[1]
    await state.update_data(mode=mode)
    await state.set_state(SwapForm.waiting_confirm)
    await callback.message.edit_text(f"Всё готово!\nФото: ✅\nВидео: ✅\nРежим: {MODE_LABELS[mode]}",
                                     reply_markup=build_confirm_keyboard())
    await callback.answer()


@router.message(SwapForm.waiting_mode)
async def wrong_mode_handler(message: Message) -> None:
    """Обрабатывает неверный тип режима наложения: кнопка не нажата"""
    await message.answer("Выберите с помощью кнопки")


@router.callback_query(SwapForm.waiting_confirm, F.data.startswith("confirm:"))
async def confirm_handler(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Получает подтверждение на создание дипфейка или отказ"""
    create_deepfake = callback.data.split(":")[1] == "create"
    await callback.answer()

    data = await state.get_data()
    await state.clear()

    if create_deepfake:
        await callback.message.edit_text("Скачиваю файлы...")
        new_job_path = create_job_dir()

        try:
            try:
                source_path, video_path = await download_inputs(bot, new_job_path, data["photo_file_id"],
                                                                data["video_file_id"])
            except (TelegramAPIError, TimeoutError) as e:
                await callback.message.edit_text("Не удалось скачать файлы. Попробуй ещё раз: /new")
                print(e)
                return

            output_path = new_job_path / OUTPUT_FILENAME
            await callback.message.edit_text("Обрабатываю видео, это займёт пару минут...")

            last_update = 0

            async def update_progress(stage: str, percent: int) -> None:
                """Редактирует сообщение относительно прогресса генерации"""
                nonlocal last_update
                if stage != "processing":
                    return
                if time.monotonic() - last_update < UPDATE_PERCENT_TIME:
                    return
                last_update = time.monotonic()
                try:
                    await callback.message.edit_text(f"Обрабатываю видео: {percent}%")
                except TelegramAPIError:
                    pass

            try:
                await run_facefusion(source_path, video_path, output_path, face_selector_mode=data["mode"],
                                     on_progress=update_progress)
            except (FileNotFoundError, RuntimeError) as e:
                print(e)
                await callback.message.edit_text("Не удалось обработать видео. Попробуй ещё раз: /new")
                return

            await callback.message.edit_text("Отправляю видео в чат...")

            try:
                await bot.send_video(
                    callback.message.chat.id,
                    BufferedInputFile(output_path.read_bytes(), filename="result.mp4"),
                    request_timeout=FILE_UPLOAD_TIMEOUT,
                )

            except TelegramAPIError as e:
                print(e)
                await callback.message.edit_text("Не удалось отправить результат")
                return

            await callback.message.edit_text("Готово!")

        finally:
            shutil.rmtree(new_job_path, ignore_errors=True)
    else:
        await callback.message.edit_text("Отменено")


@router.message(SwapForm.waiting_confirm)
async def wrong_confirm_handler(message: Message) -> None:
    """Обрабатывает неверный тип подтверждения: кнопка не нажата"""
    await message.answer("Выберите с помощью кнопки")
