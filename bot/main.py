import asyncio

from aiogram import Router, Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from bot.settings import BOT_TOKEN, ALLOWED_USER_IDS, MAX_VIDEO_SIZE, MAX_VIDEO_DURATION

router = Router()
router.message.filter(F.from_user.id.in_(ALLOWED_USER_IDS))


class SwapForm(StatesGroup):
    waiting_face = State()
    waiting_video = State()
    waiting_mode = State()
    waiting_confirm = State()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Присылает приветственное сообщение"""
    await message.answer(f"Привет, {message.from_user.first_name}")


@router.message(Command("cancel"), SwapForm)
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """Отменяет операцию создания дипфейка"""
    await state.clear()
    await message.answer("Отменено")


@router.message(Command("new"))
async def new_handler(message: Message, state: FSMContext) -> None:
    """Начинает 1 этап создания дипфейка: ожидает приема фото"""
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
        await message.answer(f"Размер видео превышает допустимое значение {MAX_VIDEO_SIZE//2**20}мб")
        return
    if message.video.duration is None or message.video.duration > MAX_VIDEO_DURATION:
        await message.answer(f"Длительность видео превышает допустимое значение {MAX_VIDEO_DURATION}с")
        return
    video_file_id = message.video.file_id
    await state.update_data(video_file_id=video_file_id)
    await state.set_state(SwapForm.waiting_mode)
    await message.answer("Видео принято, выберите режим наложения лиц")


@router.message(SwapForm.waiting_video)
async def wrong_video_handler(message: Message) -> None:
    """Обрабатывает неверный тип файла: пришло не видео"""
    await message.answer("Нужно именно видео")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
