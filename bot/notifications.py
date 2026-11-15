import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

logger = logging.getLogger(__name__)


async def update_message_text(bot: Bot, chat_id: int, message_id: int, text: str) -> None:
    """Изменяет сообщение бота"""
    try:
        await bot.edit_message_text(chat_id=chat_id, text=text, message_id=message_id)
    except TelegramAPIError as e:
        logger.warning("Не удалось изменить сообщение бота : %s", str(e))