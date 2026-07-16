# Restoran uchun buyurtma qabul qiluvchi Telegram bot (3 tilli + Click to'lov)
# Kutubxona: aiogram 3.x
# O'rnatish: pip install aiogram

import asyncio
import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from common.i18n import language_kb, set_lang, get_lang, make_translator, LANGUAGES
from common.click_pay import generate_click_url

# ====================== SOZLAMALAR ======================
BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# Menyu: {kategoriya_key: {"category": {uz,ru,en}, "items": {item_key: {"name": {uz,ru,en}, "price": N}}}}
MENU = {
    "starters": {
        "category": {"uz": "🍲 Birinchi taomlar", "ru": "🍲 Первые блюда", "en": "🍲 Starters"},
        "items": {
            "lagman": {"name": {"uz": "Lag'mon", "ru": "Лагман", "en": "Lagman"}, "price": 25000},
            "shorva": {"name": {"uz": "Sho'rva", "ru": "Шурпа", "en": "Shorva soup"}, "price": 20000},
        },
    },
    "mains": {
        "category": {"uz": "🍛 Ikkinchi taomlar", "ru": "🍛 Вторые блюда", "en": "🍛 Main dishes"},
        "items": {
            "osh": {"name": {"uz": "Osh", "ru": "Плов", "en": "Plov (Osh)"}, "price": 35000},
            "manti": {"name": {"uz": "Manti (5 dona)", "ru": "Манты (5 шт)", "en": "Manti (5 pcs)"}, "price": 30000},
            "shashlik": {"name": {"uz": "Shashlik (2 sixi)", "ru": "Шашлык (2 шт)", "en": "Shashlik (2 skewers)"}, "price": 40000},
        },
    },
    "drinks": {
        "category": {"uz": "🥤 Ichimliklar", "ru": "🥤 Напитки", "en": "🥤 Drinks"},
        "items": {
            "cola": {"name": {"uz": "Kola 0.5L", "ru": "Кола 0.5Л", "en": "Cola 0.5L"}, "price": 8000},
            "water": {"name": {"uz": "Suv 0.5L", "ru": "Вода 0.5Л", "en": "Water 0.5L"}, "price": 4000},
        },
    },
}

TR = {
    "choose_lang": {
        "uz": "Tilni tanlang / Выберите язык / Choose your language:",
        "ru": "Tilni tanlang / Выберите язык / Choose your language:",
        "en": "Tilni tanlang / Выберите язык / Choose your language:",
    },
    "welcome": {
        "uz": "Assalomu alaykum! 🍽 Restoranimiz botiga xush kelibsiz.\nKategoriyani tanlang:",
        "ru": "Здравствуйте! 🍽 Добро пожаловать в бот нашего ресторана.\nВыберите категорию:",
        "en": "Hello! 🍽 Welcome to our restaurant bot.\nChoose a category:",
    },
    "cart_btn": {"uz": "🛒 Savatcha", "ru": "🛒 Корзина", "en": "🛒 Cart"},
    "checkout_btn": {"uz": "✅ Buyurtma berish", "ru": "✅ Оформить заказ", "en": "✅ Checkout"},
    "item_added": {"uz": "{item} savatchaga qo'shildi ✅", "ru": "{item} добавлен в корзину ✅", "en": "{item} added to cart ✅"},
    "cart_empty": {"uz": "Savatchangiz bo'sh.", "ru": "Ваша корзина пуста.", "en": "Your cart is empty."},
    "cart_total": {"uz": "\nJami: {total} so'm", "ru": "\nИтого: {total} сум", "en": "\nTotal: {total} UZS"},
    "checkout_empty": {"uz": "Savatchangiz bo'sh. Avval taom tanlang.", "ru": "Ваша корзина пуста. Сначала выберите блюдо.", "en": "Your cart is empty. Please choose a dish first."},
    "ask_payment": {"uz": "To'lov turini tanlang:", "ru": "Выберите способ оплаты:", "en": "Choose a payment method:"},
    "pay_cash": {"uz": "💵 Naqd (yetkazib berishda)", "ru": "💵 Наличные (при доставке)", "en": "💵 Cash on delivery"},
    "pay_click": {"uz": "💳 Click orqali", "ru": "💳 Через Click", "en": "💳 Pay with Click"},
    "ask_phone": {"uz": "Telefon raqamingizni yuboring:", "ru": "Отправьте свой номер телефона:", "en": "Please send your phone number:"},
    "phone_btn": {"uz": "📞 Telefon raqamni yuborish", "ru": "📞 Отправить номер телефона", "en": "📞 Share phone number"},
    "ask_address": {"uz": "Yetkazib berish manzilingizni yozing:", "ru": "Напишите адрес доставки:", "en": "Please enter your delivery address:"},
    "order_done": {"uz": "Buyurtmangiz qabul qilindi! ✅", "ru": "Ваш заказ принят! ✅", "en": "Your order has been placed! ✅"},
    "phone_label": {"uz": "Telefon", "ru": "Телефон", "en": "Phone"},
    "address_label": {"uz": "Manzil", "ru": "Адрес", "en": "Address"},
    "operator_note": {"uz": "Tez orada operatorimiz siz bilan bog'lanadi.", "ru": "Наш оператор скоро свяжется с вами.", "en": "Our operator will contact you shortly."},
    "click_link_msg": {"uz": "To'lov uchun quyidagi havolani bosing:", "ru": "Нажмите на ссылку ниже для оплаты:", "en": "Tap the link below to pay:"},
    "click_paid_btn": {"uz": "✅ To'ladim", "ru": "✅ Я оплатил", "en": "✅ I've paid"},
    "click_wait_admin": {"uz": "Rahmat! To'lovingiz administrator tomonidan tekshirilmoqda.", "ru": "Спасибо! Ваш платёж проверяется администратором.", "en": "Thank you! Your payment is being verified by the admin."},
}
t = make_translator(TR)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

carts: dict[int, dict[str, list]] = {}  # {user_id: {item_key: [category_key, price, qty]}}
order_counter = 0


class Order(StatesGroup):
    waiting_phone = State()
    waiting_address = State()
    waiting_click_confirm = State()


def main_menu_kb(user_id: int):
    lang = get_lang(user_id)
    kb = [[KeyboardButton(text=MENU[cat]["category"][lang])] for cat in MENU]
    kb.append([KeyboardButton(text=t(user_id, "cart_btn")), KeyboardButton(text=t(user_id, "checkout_btn"))])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def category_by_label(user_id: int, label: str):
    lang = get_lang(user_id)
    for key, info in MENU.items():
        if info["category"][lang] == label:
            return key
    return None


def items_kb(user_id: int, category_key: str):
    lang = get_lang(user_id)
    kb = []
    for item_key, item in MENU[category_key]["items"].items():
        name = item["name"][lang]
        kb.append([InlineKeyboardButton(text=f"{name} — {item['price']} so'm", callback_data=f"add:{category_key}:{item_key}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def payment_kb(user_id: int):
    kb = [
        [InlineKeyboardButton(text=t(user_id, "pay_cash"), callback_data="pay:cash")],
        [InlineKeyboardButton(text=t(user_id, "pay_click"), callback_data="pay:click")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def cart_text(user_id: int) -> str:
    lang = get_lang(user_id)
    cart = carts.get(user_id, {})
    if not cart:
        return t(user_id, "cart_empty")
    lines, total = [], 0
    for item_key, (cat_key, price, qty) in cart.items():
        name = MENU[cat_key]["items"][item_key]["name"][lang]
        subtotal = price * qty
        total += subtotal
        lines.append(f"• {name} x{qty} = {subtotal} so'm")
    lines.append(t(user_id, "cart_total", total=total))
    return "\n".join(lines)


def cart_total(user_id: int) -> int:
    return sum(price * qty for _, price, qty in carts.get(user_id, {}).values())


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    carts.setdefault(message.from_user.id, {})
    await message.answer(t(message.from_user.id, "choose_lang"), reply_markup=language_kb())


@router.callback_query(F.data.startswith("lang:"))
async def choose_lang(callback: CallbackQuery):
    lang = callback.data.split(":", 1)[1]
    set_lang(callback.from_user.id, lang)
    await callback.message.answer(t(callback.from_user.id, "welcome"), reply_markup=main_menu_kb(callback.from_user.id))
    await callback.answer()


@router.message(F.text.func(lambda text: True))
async def route_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text == t(user_id, "cart_btn"):
        await message.answer(cart_text(user_id))
        return
    if message.text == t(user_id, "checkout_btn"):
        await checkout_start(message, state)
        return
    cat_key = category_by_label(user_id, message.text)
    if cat_key:
        await message.answer(message.text, reply_markup=items_kb(user_id, cat_key))
        return
    # boshqa matnlar Order holatlarida handler'lar orqali qayta ishlanadi (pastda ro'yxatdan o'tgan)


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    _, cat_key, item_key = callback.data.split(":", 2)
    price = MENU[cat_key]["items"][item_key]["price"]
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    name = MENU[cat_key]["items"][item_key]["name"][lang]
    cart = carts.setdefault(user_id, {})
    if item_key in cart:
        cart[
