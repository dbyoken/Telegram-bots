# Onlayn kurs sotish uchun Telegram bot (3 tilli + Click to'lov)
# Mijoz kursni tanlaydi -> Click orqali yoki karta o'tkazmasi orqali to'laydi ->
# (karta uchun) chek yuboradi -> admin tasdiqlaydi -> mijozga kurs havolasi yuboriladi
# Kutubxona: aiogram 3.x
# O'rnatish: pip install aiogram

import asyncio
import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from common.i18n import language_kb, set_lang, get_lang, make_translator
from common.click_pay import generate_click_url

# ====================== SOZLAMALAR ======================
BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

CARD_NUMBER = "8600 0000 0000 0000"
CARD_OWNER = "F.I.Sh."

COURSES = {
    "smm": {
        "name": {"uz": "📊 SMM asoslari", "ru": "📊 Основы SMM", "en": "📊 SMM Basics"},
        "desc": {
            "uz": "Ijtimoiy tarmoqlarda targ'ibot qilishni o'rganing. 4 hafta, video darslar.",
            "ru": "Научитесь продвижению в соцсетях. 4 недели, видеоуроки.",
            "en": "Learn social media promotion. 4 weeks, video lessons.",
        },
        "price": 250000,
        "link": "https://t.me/+kurs_smm_invite",
    },
    "python": {
        "name": {"uz": "💻 Python dasturlash", "ru": "💻 Программирование на Python", "en": "💻 Python Programming"},
        "desc": {
            "uz": "0 dan Python dasturlashni o'rganing. 8 hafta, amaliy loyihalar bilan.",
            "ru": "Изучите Python с нуля. 8 недель, с практическими проектами.",
            "en": "Learn Python from scratch. 8 weeks, with hands-on projects.",
        },
        "price": 400000,
        "link": "https://t.me/+kurs_python_invite",
    },
    "freelance": {
        "name": {"uz": "📈 Frilanser bo'lish", "ru": "📈 Как стать фрилансером", "en": "📈 Becoming a Freelancer"},
        "desc": {
            "uz": "Frilans platformalarda ishlashni boshlash. 3 hafta.",
            "ru": "Начните работать на фриланс-платформах. 3 недели.",
            "en": "Start working on freelance platforms. 3 weeks.",
        },
        "price": 200000,
        "link": "https://t.me/+kurs_frilans_invite",
    },
}

TR = {
    "welcome": {
        "uz": "Assalomu alaykum! 🎓 Onlayn kurslarimizga xush kelibsiz.\nQiziqqan kursingizni tanlang:",
        "ru": "Здравствуйте! 🎓 Добро пожаловать на наши онлайн-курсы.\nВыберите интересующий вас курс:",
        "en": "Hello! 🎓 Welcome to our online courses.\nChoose the course you're interested in:",
    },
    "price_label": {"uz": "Narxi", "ru": "Цена", "en": "Price"},
    "ask_payment": {"uz": "To'lov turini tanlang:", "ru": "Выберите способ оплаты:", "en": "Choose a payment method:"},
    "pay_click": {"uz": "💳 Click orqali (avtomatik)", "ru": "💳 Через Click (автоматически)", "en": "💳 Pay with Click (automatic)"},
    "pay_card": {"uz": "🏦 Karta o'tkazmasi", "ru": "🏦 Перевод на карту", "en": "🏦 Bank card transfer"},
    "click_link_msg": {"uz": "To'lov uchun quyidagi havolani bosing:", "ru": "Нажмите на ссылку ниже для оплаты:", "en": "Tap the link below to pay:"},
    "click_paid_btn": {"uz": "✅ To'ladim", "ru": "✅ Я оплатил", "en": "✅ I've paid"},
    "click_wait_admin": {"uz": "Rahmat! To'lovingiz tekshirilmoqda, tasdiqlangach kurs havolasi yuboriladi.", "ru": "Спасибо! Ваш платёж проверяется, ссылка на курс придёт после подтверждения.", "en": "Thank you! Your payment is being checked; the course link will be sent once confirmed."},
    "card_info": {
        "uz": "To'lov qilish uchun quyidagi kartaga o'tkazing:\n💳 {card}\n👤 {owner}\n\nTo'lovni amalga oshirgach, chek (skrinshot) rasmini shu yerga yuboring.",
        "ru": "Для оплаты переведите на карту:\n💳 {card}\n👤 {owner}\n\nПосле оплаты отправьте сюда скриншот чека.",
        "en": "To pay, transfer to this card:\n💳 {card}\n👤 {owner}\n\nAfter paying, send a screenshot of the receipt here.",
    },
    "screenshot_received": {
        "uz": "Chekingiz qabul qilindi ✅\nAdministrator tekshirgach, kursga kirish havolasi yuboriladi. Iltimos, biroz kuting.",
        "ru": "Ваш чек получен ✅\nПосле проверки администратором вам будет отправлена ссылка на курс. Пожалуйста, подождите.",
        "en": "Your receipt has been received ✅\nOnce the admin verifies it, you'll receive the course access link. Please wait.",
    },
    "payment_confirmed": {
        "uz": "✅ To'lovingiz tasdiqlandi!\n\n\"{course}\" kursiga xush kelibsiz.\nKursga kirish havolasi: {link}",
        "ru": "✅ Ваш платёж подтверждён!\n\nДобро пожаловать на курс \"{course}\".\nСсылка для доступа: {link}",
        "en": "✅ Your payment has been confirmed!\n\nWelcome to the \"{course}\" course.\nAccess link: {link}",
    },
    "payment_rejected": {
        "uz": "❌ To'lovingiz tasdiqlanmadi. Iltimos, to'g'ri chek yuboring yoki administrator bilan bog'laning.",
        "ru": "❌ Ваш платёж не подтверждён. Пожалуйста, отправьте корректный чек или свяжитесь с администратором.",
        "en": "❌ Your payment was not confirmed. Please send a valid receipt or contact the admin.",
    },
}
t = make_translator(TR)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Tasdiqlanishi kutilayotgan buyurtmalar: {user_id: course_key}
pending_orders: dict[int, str] = {}
order_counter = 0


class Purchase(StatesGroup):
    choosing_payment = State()
    waiting_screenshot = State()
    waiting_click_confirm = State()


def courses_kb(user_id: int):
    lang = get_lang(user_id)
    kb = []
    for key, info in COURSES.items():
        kb.append([InlineKeyboardButton(text=f"{info['name'][lang]} — {info['price']} so'm", callback_data=f"course:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def payment_kb(user_id: int):
    kb = [
        [InlineKeyboardButton(text=t(user_id, "pay_click"), callback_data="pay:click")],
        [InlineKeyboardButton(text=t(user_id, "pay_card"), callback_data="pay:card")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Tilni tanlang / Выберите язык / Choose your language:", reply_markup=language_kb())


@router.callback_query(F.data.startswith("lang:"))
async def choose_lang(callback: CallbackQuery):
    lang = callback.data.split(":", 1)[1]
    set_lang(callback.from_user.id, lang)
    await callback.message.answer(t(callback.from_user.id, "welcome"), reply_markup=courses_kb(callback.from_user.id))
    await callback.answer()


@router.callback_query(F.data.startswith("course:"))
async def show_course(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    info = COURSES[key]
    await state.update_data(course_key=key)
    await callback.message.answer(
        f"{info['name'][lang]}\n\n{info['desc'][lang]}\n\n{t(user_id, 'price_label')}: {info['price']} so'm"
    )
    await callback.message.answer(t(user_id, "ask_payment"), reply_markup=payment_kb(user_id))
    await state.set_state(Purchase.choosing_payment)
    await callback.answer()


@router.callback_query(Purchase.choosing_payment, F.data.startswith("pay:"))
async def choose_payment(callback: CallbackQuery, state: FSMContext):
    global order_counter
    method = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    data = await state.get_data()
    course_key = data["course_key"]
    info = COURSES[course_key]

    if method == "click":
        order_counter += 1
        order_id = f"COURSE-{order_counter}-{user_id}"
        link = generate_click_url(info["price"], order_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(user_id, "click_paid_btn"), callback_data=f"clickpaid:{course_key}")]
        ])
        await callback.message.answer(f"{t(user_id, 'click_link_msg')}\n{link}", reply_markup=kb)
        await state.set_state(Purchase.waiting_click_confirm)
    else:
        await callback.message.answer(t(user_id, "card_info", card=CARD_NUMBER, owner=CARD_OWNER))
        await state.set_state(Purchase.waiting_screenshot)
    await callback.answer()


@router.message(Purchase.waiting_screenshot, F.photo)
async def receive_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    course_key = data.get("course_key")
    user_id = message.from_user.id
    lang = get_lang(user_id)
    pending_orders[user_id] = course_key

    await message.answer(t(user_id, "screenshot_received"))

    if ADMIN_CHAT_ID:
        await bot.send_photo(
            ADMIN_CHAT_ID,
            photo=message.photo[-1].file_id,
            caption=(
                f"🆕 Yangi to'lov (karta)!\n\nKurs: {COURSES[course_key]['name'][lang]}\n"
                f"Mijoz: @{message.from_user.username or user_id} (ID: {user_id})\n\n"
                f"Tasdiqlash: /tasdiqla {user_id}\nRad etish: /radetish {user_id}"
            ),
        )
    await state.clear()


@router.callback_query(F.data.startswith("clickpaid:"))
async def click_paid(callback: CallbackQuery, state: FSMContext):
    course_key = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    pending_orders[user_id] = course_key

    await callback.message.answer(t(user_id, "click_wait_admin"))

    if ADMIN_CHAT_ID:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"🆕 Yangi to'lov (Click)!\n\nKurs: {COURSES[course_key]['name'][lang]} "
            f"({COURSES[course_key]['price']} so'm — Click orqali to'landi, tekshiring)\n"
            f"Mijoz: @{callback.from_user.username or user_id} (ID: {user_id})\n\n"
            f"Tasdiqlash: /tasdiqla {user_id}\nRad etish: /radetish {user_id}",
        )
    await state.clear()
    await callback.answer()


@router.message(Command("tasdiqla"))
async def confirm_payment(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID and message.chat.id != ADMIN_CHAT_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /tasdiqla <user_id>")
        return
    user_id = int(parts[1])
    course_key = pending_orders.pop(user_id, None)
    if not course_key:
        await message.answer("Bu foydalanuvchi uchun kutilayotgan buyurtma topilmadi.")
        return
    lang = get_lang(user_id)
    info = COURSES[course_key]
    await bot.send_message(user_id, t(user_id, "payment_confirmed", course=info["name"][lang], link=info["link"]))
    await message.answer(f"Foydalanuvchi {user_id} ga kurs havolasi yuborildi.")


@router.message(Command("radetish"))
async def reject_payment(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID and message.chat.id != ADMIN_CHAT_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /radetish <user_id>")
        return
    user_id = int(parts[1])
    if pending_orders.pop(user_id, None) is None:
        await message.answer("Bu foydalanuvchi uchun kutilayotgan buyurtma topilmadi.")
        return
    await bot.send_message(user_id, t(user_id, "payment_rejected"))
    await message.answer(f"Foydalanuvchi {user_id} ga rad javobi yuborildi.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
