# Xizmat ko'rsatish (usta, salon va h.k.) uchun bandlov boti (3 tilli + Click to'lov)
# Kutubxona: aiogram 3.x
# O'rnatish: pip install aiogram

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta

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

SERVICES = {
    "haircut": {"name": {"uz": "💇 Soch olish", "ru": "💇 Стрижка", "en": "💇 Haircut"}, "price": 40000},
    "manicure": {"name": {"uz": "💅 Manikyur", "ru": "💅 Маникюр", "en": "💅 Manicure"}, "price": 60000},
    "plumbing": {"name": {"uz": "🔧 Santexnika ta'mirlash", "ru": "🔧 Ремонт сантехники", "en": "🔧 Plumbing repair"}, "price": 100000},
    "carwash": {"name": {"uz": "🚗 Avto yuvish", "ru": "🚗 Автомойка", "en": "🚗 Car wash"}, "price": 50000},
}

TIME_SLOTS = ["09:00", "11:00", "13:00", "15:00", "17:00", "19:00"]

TR = {
    "welcome": {
        "uz": "Assalomu alaykum! 🧰 Xizmatlarimizdan birini tanlab, band qilishingiz mumkin.\nXizmatni tanlang:",
        "ru": "Здравствуйте! 🧰 Выберите одну из наших услуг для записи.\nВыберите услугу:",
        "en": "Hello! 🧰 Choose one of our services to book.\nSelect a service:",
    },
    "choose_date": {"uz": "Qaysi sanaga yozilmoqchisiz?", "ru": "На какую дату хотите записаться?", "en": "Which date would you like to book?"},
    "choose_time": {"uz": "Soatni tanlang:", "ru": "Выберите время:", "en": "Choose a time:"},
    "ask_payment": {"uz": "To'lov turini tanlang:", "ru": "Выберите способ оплаты:", "en": "Choose a payment method:"},
    "pay_cash": {"uz": "💵 Joyida naqd", "ru": "💵 Наличными на месте", "en": "💵 Cash on site"},
    "pay_click": {"uz": "💳 Click orqali", "ru": "💳 Через Click", "en": "💳 Pay with Click"},
    "ask_phone": {"uz": "Bog'lanish uchun telefon raqamingizni yuboring:", "ru": "Отправьте номер телефона для связи:", "en": "Please send your contact phone number:"},
    "phone_btn": {"uz": "📞 Telefon raqamni yuborish", "ru": "📞 Отправить номер телефона", "en": "📞 Share phone number"},
    "confirmed": {"uz": "✅ Bandlov tasdiqlandi!", "ru": "✅ Запись подтверждена!", "en": "✅ Booking confirmed!"},
    "service_label": {"uz": "Xizmat", "ru": "Услуга", "en": "Service"},
    "price_label": {"uz": "Narx", "ru": "Цена", "en": "Price"},
    "date_label": {"uz": "Sana", "ru": "Дата", "en": "Date"},
    "time_label": {"uz": "Vaqt", "ru": "Время", "en": "Time"},
    "phone_label": {"uz": "Telefon", "ru": "Телефон", "en": "Phone"},
    "book_again": {"uz": "Yana xizmat band qilish uchun /start bosing.", "ru": "Чтобы записаться ещё раз, нажмите /start.", "en": "To book another service, press /start."},
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

booking_counter = 0


class Booking(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    choosing_payment = State()
    waiting_phone = State()
    waiting_click_confirm = State()


def services_kb(user_id: int):
    lang = get_lang(user_id)
    kb = []
    for key, info in SERVICES.items():
        kb.append([InlineKeyboardButton(text=f"{info['name'][lang]} — {info['price']} so'm", callback_data=f"svc:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def dates_kb():
    kb = []
    today = datetime.now()
    for i in range(7):
        day = today + timedelta(days=i)
        label = day.strftime("%d-%m (%a)")
        kb.append([InlineKeyboardButton(text=label, callback_data=f"date:{day.strftime('%d-%m-%Y')}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def times_kb():
    kb = [[InlineKeyboardButton(text=tm, callback_data=f"time:{tm}")] for tm in TIME_SLOTS]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def payment_kb(user_id: int):
    kb = [
        [InlineKeyboardButton(text=t(user_id, "pay_cash"), callback_data="pay:cash")],
        [InlineKeyboardButton(text=t(user_id, "pay_click"), callback_data="pay:click")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Tilni tanlang / Выберите язык / Choose your language:", reply_markup=language_kb())


@router.callback_query(F.data.startswith("lang:"))
async def choose_lang(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":", 1)[1]
    set_lang(callback.from_user.id, lang)
    await callback.message.answer(t(callback.from_user.id, "welcome"), reply_markup=services_kb(callback.from_user.id))
    await state.set_state(Booking.choosing_service)
    await callback.answer()


@router.callback_query(Booking.choosing_service, F.data.startswith("svc:"))
async def choose_service(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    await state.update_data(service_key=key, service_name=SERVICES[key]["name"][lang], price=SERVICES[key]["price"])
    await state.set_state(Booking.choosing_date)
    await callback.message.answer(t(user_id, "choose_date"), reply_markup=dates_kb())
    await callback.answer()


@router.callback_query(Booking.choosing_date, F.data.startswith("date:"))
async def choose_date(callback: CallbackQuery, state: FSMContext):
    date = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    await state.update_data(date=date)
    await state.set_state(Booking.choosing_time)
    await callback.message.answer(t(user_id, "choose_time"), reply_markup=times_kb())
    await callback.answer()


@router.callback_query(Booking.choosing_time, F.data.startswith("time:"))
async def choose_time(callback: CallbackQuery, state: FSMContext):
    time_slot = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    await state.update_data(time=time_slot)
    await state.set_state(Booking.choosing_payment)
    await callback.message.answer(t(user_id, "ask_payment"), reply_markup=payment_kb(user_id))
    await callback.answer()


@router.callback_query(Booking.choosing_payment, F.data.startswith("pay:"))
async def choose_payment(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    await state.update_data(payment_method=method)
    await state.set_state(Booking.waiting_phone)
    phone_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(user_id, "phone_btn"), request_contact=True)]],
        resize_keyboard=True,
    )
    await callback.message.answer(t(user_id, "ask_phone"), reply_markup=phone_kb)
    await callback.answer()


@router.message(Booking.waiting_phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    global booking_counter
    data = await state.update_data(phone=message.contact.phone_number)
    user_id = message.from_user.id
    booking_counter += 1
    booking_id = f"SVC-{booking_counter}"

    summary = (
        f"{t(user_id, 'service_label')}: {data['service_name']}\n"
        f"{t(user_id, 'price_label')}: {data['price']} so'm\n"
        f"{t(user_id, 'date_label')}: {data['date']}\n"
        f"{t(user_id, 'time_label')}: {data['time']}\n"
        f"{t(user_id, 'phone_label')}: {data['phone']}"
    )

    if data["payment_method"] == "click":
        link = generate_click_url(data["price"], booking_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, "click_paid_btn"), callback_data=f"clickpaid:{booking_id}")]
        ])
        await message.answer(f"{t(user_id, 'click_link_msg')}\n{link}", reply_markup=kb)
        await state.set_state(Booking.waiting_click_confirm)
    else:
        await message.answer(f"{t(user_id, 'confirmed')}\n\n{summary}")
        if ADMIN_CHAT_ID:
            await bot.send_message(
                ADMIN_CHAT_ID,
                f"🆕 Yangi bandlov [{booking_id}] (naqd)\n\n{summary}\n"
                f"Mijoz: @{message.from_user.username or user_id}",
            )
        await state.clear()
        await message.answer(t(user_id, "book_again"))


@router.callback_query(F.data.startswith("clickpaid:"))
async def click_paid(callback: CallbackQuery, state: FSMContext):
    booking_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    data = await state.get_data()

    summary = (
        f"{t(user_id, 'service_label')}: {data.get('service_name','-')}\n"
        f"{t(user_id, 'price_label')}: {data.get('price','-')} so'm\n"
        f"{t(user_id, 'date_label')}: {data.get('date','-')}\n"
        f"{t(user_id, 'time_label')}: {data.get('time','-')}\n"
        f"{t(user_id, 'phone_label')}: {data.get('phone','-')}"
    )

    await callback.message.answer(t(user_id, "click_wait_admin"))

    if ADMIN_CHAT_ID:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"🆕 Yangi bandlov [{booking_id}] (Click — tasdiqlashni tekshiring)\n\n{summary}\n"
            f"Mijoz: @{callback.from_user.username or user_id}",
        )
    await state.clear()
    await callback.message.answer(t(user_id, "book_again"))
    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
