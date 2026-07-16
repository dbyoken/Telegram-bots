# Umumiy til (i18n) moduli — barcha botlar shu modulni ishlatadi.
# 3 til: O'zbek (uz), Rus (ru), Ingliz (en)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LANGUAGES = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

DEFAULT_LANG = "uz"

# Har bir foydalanuvchining tanlagan tili: {user_id: "uz"/"ru"/"en"}
_user_lang: dict[int, str] = {}


def set_lang(user_id: int, lang: str) -> None:
    _user_lang[user_id] = lang


def get_lang(user_id: int) -> str:
    return _user_lang.get(user_id, DEFAULT_LANG)


def language_kb() -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text=name, callback_data=f"lang:{code}")] for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def make_translator(translations: dict):
    """
    translations = {
        "greeting": {"uz": "...", "ru": "...", "en": "..."},
        ...
    }
    Qaytaradi: t(user_id, key, **kwargs) -> tarjima qilingan matn
    """
    def t(user_id: int, key: str, **kwargs) -> str:
        lang = get_lang(user_id)
        entry = translations.get(key, {})
        text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
        return text.format(**kwargs) if kwargs else text
    return t
