from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

MODE_LABELS = {
    "one": "Одно лицо",
    "many": "Все лица",
    "reference": "Референс",
}

CONFIRM_LABELS = {
    "create": "Заменить лицо",
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
    """Создает инлайн кнопку для подтверждения создания дипфейка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=CONFIRM_LABELS["create"], callback_data="confirm:create"),
        ]
    ])
    return keyboard


def build_start_keyboard() -> ReplyKeyboardMarkup:
    """Создает кнопку 'Заменить лицо' на клавиатуре"""
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text=CONFIRM_LABELS["create"])
        ]
    ],
        resize_keyboard=True,
        is_persistent=True)
    return keyboard


def build_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Создает кнопку 'Отмена' на клавиатуре"""
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text=CONFIRM_LABELS["cancel"])
        ]
    ],
        resize_keyboard=True,
        is_persistent=True)
    return keyboard
