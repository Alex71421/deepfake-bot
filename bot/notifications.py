from aiogram import Bot
from aiogram.exceptions import TelegramAPIError


async def update_message_text(bot: Bot, chat_id: int, message_id: int, text: str) -> None:
    """Изменяет сообщение бота"""
    try:
        await bot.edit_message_text(chat_id=chat_id, text=text, message_id=message_id)
    except TelegramAPIError as e:
        print(type(e).__name__, str(e))