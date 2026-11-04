from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

MODE_LABELS = {
    "one": "Одно лицо",
    "many": "Все лица",
    "reference": "Референс",
}

CONFIRM_LABELS = {
    "create": "Создать дипфейк",
    "cancel": "Отмена",
}


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


def build_confirm_keyboard() -> InlineKeyboardMarkup:
    """Создает инлайн кнопки для подтверждения создания дипфейка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=CONFIRM_LABELS["create"], callback_data="confirm:create"),
            InlineKeyboardButton(text=CONFIRM_LABELS["cancel"], callback_data="confirm:cancel"),
        ]
    ])
    return keyboard