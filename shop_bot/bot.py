# Onlayn do'kon uchun buyurtma qabul qiluvchi Telegram bot (3 tilli + Click to'lov)
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

from common.i18n import language_kb, set_lang, get_lang, make_translator
from common.click_pay import generate_click_url

# ====================== SOZLAMALAR ======================
BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

CATALOG = {
    "clothes": {
        "category": {"uz": "👕 Kiyimlar", "ru": "👕 Одежда", "en": "👕 Clothes"},
        "items": {
            "tshirt": {"name": {"uz": "Futbolka", "ru": "Футболка", "en": "T-shirt"}, "price": 120000},
            "pants": {"name": {"uz": "Shim", "ru": "Брюки", "en": "Pants"}, "price": 180000},
        },
    },
    "shoes": {
        "category": {"uz": "👟 Poyabzallar", "ru": "👟 Обувь", "en": "👟 Shoes"},
        "items": {
            "sneakers": {"name": {"uz": "Krossovka", "ru": "Кроссовки", "en": "Sneakers"}, "price": 350000},
            "loafers": {"name": {"uz": "Tufli", "ru": "Туфли", "en": "Loafers"}, "price": 280000},
        },
    },
    "accessories": {
        "category": {"uz": "🎒 Aksessuarlar", "ru": "🎒 Аксессуары", "en": "🎒 Accessories"},
        "items": {
            "backpack": {"name": {"uz": "Ryukzak", "ru": "Рюкзак", "en": "Backpack"}, "price": 150000},
            "watch": {"name": {"uz": "Soat", "ru": "Часы", "en": "Watch"}, "price": 200000},
        },
    },
}

TR = {
    "choose_lang": {"uz": "Tilni tanlang / Выберите язык / Choose your language:", "ru": "", "en": ""},
    "welcome": {
        "uz": "Assalomu alaykum! 🛍 Onlayn do'konimizga xush kelibsiz.\nKategoriyani tanlang:",
        "ru": "Здравствуйте! 🛍 Добро пожаловать в наш онлайн-магазин.\nВыберите категорию:",
        "en": "Hello! 🛍 Welcome to our online store.\nChoose a category:",
    },
    "cart_btn": {"uz": "🛒 Savatcha", "ru": "🛒 Корзина", "en": "🛒 Cart"},
    "checkout_btn": {"uz": "✅ Buyurtma berish", "ru": "✅ Оформить заказ", "en": "✅ Checkout"},
    "item_added": {"uz": "{item} savatchaga qo'shildi ✅", "ru": "{item} добавлен в корзину ✅", "en": "{item} added to cart ✅"},
    "cart_empty": {"uz": "Savatchangiz bo'sh.", "ru": "Ваша корзина пуста.", "en": "Your cart is empty."},
    "cart_total": {"uz": "\nJami: {total} so'm", "ru": "\nИтого: {total} сум", "en": "\nTotal: {total} UZS"},
    "checkout_empty": {"uz": "Savatchangiz bo'sh. Avval mahsulot tanlang.", "ru": "Ваша корзина пуста. Сначала выберите товар.", "en": "Your cart is empty. Please choose a product first."},
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

carts: dict[int, dict[str, list]] = {}
order_counter = 0


class Order(StatesGroup):
    waiting_phone = State()
    waiting_address = State()
    waiting_click_confirm = State()


def main_menu_kb(user_id: int):
    lang = get_lang(user_id)
    kb = [[KeyboardButton(text=CATALOG[cat]["category"][lang])] for cat in CATALOG]
    kb.append([KeyboardButton(text=t(user_id, "cart_btn")), KeyboardButton(text=t(user_id, "checkout_btn"))])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def category_by_label(user_id: int, label: str):
    lang = get_lang(user_id)
    for key, info in CATALOG.items():
        if info["category"][lang] == label:
            return key
    return None


def items_kb(user_id: int, category_key: str):
    lang = get_lang(user_id)
    kb = []
    for item_key, item in CATALOG[category_key]["items"].items():
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
        name = CATALOG[cat_key]["items"][item_key]["name"][lang]
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
    await message.answer("Tilni tanlang / Выберите язык / Choose your language:", reply_markup=language_kb())


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


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(callback: CallbackQuery):
    _, cat_key, item_key = callback.data.split(":", 2)
    price = CATALOG[cat_key]["items"][item_key]["price"]
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    name = CATALOG[cat_key]["items"][item_key]["name"][lang]
    cart = carts.setdefault(user_id, {})
    if item_key in cart:
        cart[item_key][2] += 1
    else:
        cart[item_key] = [cat_key, price, 1]
    await callback.answer(t(user_id, "item_added", item=name))


async def checkout_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    cart = carts.get(user_id, {})
    if not cart:
        await message.answer(t(user_id, "checkout_empty"))
        return
    await message.answer(t(user_id, "ask_payment"), reply_markup=payment_kb(user_id))


@router.callback_query(F.data.startswith("pay:"))
async def choose_payment(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    await state.update_data(payment_method=method)
    await state.set_state(Order.waiting_phone)
    phone_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(user_id, "phone_btn"), request_contact=True)]],
        resize_keyboard=True,
    )
    await callback.message.answer(t(user_id, "ask_phone"), reply_markup=phone_kb)
    await callback.answer()


@router.message(Order.waiting_phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(Order.waiting_address)
    await message.answer(t(message.from_user.id, "ask_address"))


@router.message(Order.waiting_address)
async def get_address(message: Message, state: FSMContext):
    global order_counter
    data = await state.update_data(address=message.text)
    user_id = message.from_user.id
    order_summary = cart_text(user_id)
    order_counter += 1
    order_id = f"SHOP-{order_counter}"

    if data["payment_method"] == "click":
        amount = cart_total(user_id)
        link = generate_click_url(amount, order_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, "click_paid_btn"), callback_data=f"clickpaid:{order_id}")]
        ])
        await message.answer(f"{t(user_id, 'click_link_msg')}\n{link}", reply_markup=kb)
        await state.set_state(Order.waiting_click_confirm)
    else:
        await message.answer(
            f"{t(user_id, 'order_done')}\n\n{order_summary}\n\n"
            f"{t(user_id, 'phone_label')}: {data['phone']}\n{t(user_id, 'address_label')}: {data['address']}\n\n"
            f"{t(user_id, 'operator_note')}",
            reply_markup=main_menu_kb(user_id),
        )
        if ADMIN_CHAT_ID:
            await bot.send_message(
                ADMIN_CHAT_ID,
                f"🆕 Yangi buyurtma [{order_id}] (naqd)\n\n{order_summary}\n\n"
                f"Mijoz: @{message.from_user.username or user_id}\n"
                f"Telefon: {data['phone']}\nManzil: {data['address']}",
            )
        carts[user_id] = {}
        await state.clear()


@router.callback_query(F.data.startswith("clickpaid:"))
async def click_paid(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    data = await state.get_data()
    order_summary = cart_text(user_id)
    amount = cart_total(user_id)

    await callback.message.answer(t(user_id, "click_wait_admin"), reply_markup=main_menu_kb(user_id))

    if ADMIN_CHAT_ID:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"🆕 Yangi buyurtma [{order_id}] (Click, {amount} so'm — tasdiqlashni tekshiring)\n\n{order_summary}\n\n"
            f"Mijoz: @{callback.from_user.username or user_id}\n"
            f"Telefon: {data.get('phone', '-')}\nManzil: {data.get('address', '-')}",
        )
    carts[user_id] = {}
    await state.clear()
    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
