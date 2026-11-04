from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states import SwapForm


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Присылает приветственное сообщение"""
    await message.answer(f"Привет, {message.from_user.first_name}")


@router.message(Command("cancel"), SwapForm)
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """Отменяет операцию создания дипфейка"""
    await state.clear()
    await message.answer("Отменено")