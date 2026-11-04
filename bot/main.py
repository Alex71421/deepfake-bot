import asyncio

from aiogram import Router, Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot.settings import BOT_TOKEN, ALLOWED_USER_IDS, MAX_VIDEO_SIZE, MAX_VIDEO_DURATION


MODE_LABELS = {
    "one": "Одно лицо",
    "many": "Все лица",
    "reference": "Референс",
}

CONFIRM_LABELS = {
    "create": "Создать дипфейк",
    "cancel": "Отмена",
}

router = Router()
router.message.filter(F.from_user.id.in_(ALLOWED_USER_IDS))
router.callback_query.filter(F.from_user.id.in_(ALLOWED_USER_IDS))


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
        await message.answer(f"Размер видео превышает допустимое значение {MAX_VIDEO_SIZE//2**20}мб")
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


def build_mode_keyboard() -> InlineKeyboardMarkup:
    """Создает инлайн кнопки для выбора режима наложения лиц"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=MODE_LABELS["one"], callback_data="mode:one"),
            InlineKeyboardButton(text=MODE_LABELS["many"], callback_data="mode:many"),
            InlineKeyboardButton(text=MODE_LABELS["reference"], callback_data="mode:reference"),
        ]
    ])
    return keyboard


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


def build_confirm_keyboard() -> InlineKeyboardMarkup:
    """Создает инлайн кнопки для подтверждения создания дипфейка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=CONFIRM_LABELS["create"], callback_data="confirm:create"),
            InlineKeyboardButton(text=CONFIRM_LABELS["cancel"], callback_data="confirm:cancel"),
        ]
    ])
    return keyboard


@router.callback_query(SwapForm.waiting_confirm, F.data.startswith("confirm:"))
async def confirm_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Получает подтверждение на создание дипфейка или отказ"""
    create_deepfake = callback.data.split(":")[1] == "create"
    if create_deepfake:
        data = await state.get_data()
        await callback.message.edit_text("Задача принята")
        print(data)
    else:
        await callback.message.edit_text("Отменено")
    await state.clear()
    await callback.answer()


@router.message(SwapForm.waiting_confirm)
async def wrong_confirm_handler(message: Message) -> None:
    """Обрабатывает неверный тип подтверждения: кнопка не нажата"""
    await message.answer("Выберите с помощью кнопки")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
