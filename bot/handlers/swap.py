import asyncio

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.jobs import Job
from bot.keyboards import build_mode_keyboard, build_confirm_keyboard, MODE_LABELS
from bot.notifications import update_message_text
from bot.settings import MAX_VIDEO_DURATION, MAX_VIDEO_SIZE
from bot.states import SwapForm

router = Router()


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
async def confirm_handler(callback: CallbackQuery, state: FSMContext, bot: Bot, queue: asyncio.Queue    ) -> None:
    """Получает подтверждение на создание дипфейка или отказ"""
    create_deepfake = callback.data.split(":")[1] == "create"
    await callback.answer()

    data = await state.get_data()
    await state.clear()

    if create_deepfake:
        job = Job(data["photo_file_id"], data["video_file_id"], data["mode"],
                  callback.message.chat.id, callback.message.message_id)
        # queue.qsize() + 1 - чтобы избежать гонки сообщений, queue.put(job) вызывается после изменения сообщения
        await update_message_text(bot, callback.message.chat.id, callback.message.message_id,
                                  f"Задание добавлено в очередь. Позиция в очереди ожидания: {queue.qsize() + 1}")
        await queue.put(job)
    else:
        await callback.message.edit_text("Отменено")


@router.message(SwapForm.waiting_confirm)
async def wrong_confirm_handler(message: Message) -> None:
    """Обрабатывает неверный тип подтверждения: кнопка не нажата"""
    await message.answer("Выберите с помощью кнопки")


