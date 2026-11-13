from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import build_start_keyboard, CONFIRM_LABELS

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    """Присылает приветственное сообщение"""
    await state.clear()
    await message.answer(f"Привет, {message.from_user.first_name}", reply_markup=build_start_keyboard())


@router.message(Command("cancel"))
@router.message(F.text == CONFIRM_LABELS["cancel"])
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """Отменяет операцию создания замены лица"""
    if await state.get_state() is not None:
        await state.clear()
        await message.answer("Отменено", reply_markup=build_start_keyboard())
    else:
        await message.answer("Отменять нечего", reply_markup=build_start_keyboard())
