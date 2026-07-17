import asyncio
import json
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")

DATA_DIR = Path(__file__).parent
ORDERS_FILE = DATA_DIR / "active_orders.json"

BRANCHES = ["Axsikent", "Jasmin"]

router = Router()


# ---------------------------------------------------------------------------
# Persistent storage helpers (JSON, xuddi shop_bot'dagi kabi)
# ---------------------------------------------------------------------------
def load_orders() -> dict:
    if ORDERS_FILE.exists():
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"order_counter": 0, "active_orders": {}}


def save_orders(data: dict) -> None:
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# FSM holatlar
# ---------------------------------------------------------------------------
class OrderStates(StatesGroup):
    choosing_branch = State()
    choosing_items = State()
    entering_phone = State()
    entering_location = State()
    confirming = State()


class FeedbackStates(StatesGroup):
    waiting_text = State()


# ---------------------------------------------------------------------------
# Klaviaturalar
# ---------------------------------------------------------------------------
def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Buyurtma berish")],
            [
                KeyboardButton(text="ℹ️ Biz haqimizda"),
                KeyboardButton(text="🛍 Buyurtmalarim"),
            ],
            [KeyboardButton(text="🏠 Filiallar")],
            [
                KeyboardButton(text="✍️ Fikr bildirish"),
                KeyboardButton(text="⚙️ Sozlamalar"),
            ],
        ],
        resize_keyboard=True,
    )


def branch_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b)] for b in BRANCHES]
        + [[KeyboardButton(text="⬅️ Orqaga")]],
        resize_keyboard=True,
    )


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
    )


def location_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]],
        resize_keyboard=True,
    )


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        "Shox Somsa botiga xush kelibsiz.\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=main_menu_kb(),
    )


# ---------------------------------------------------------------------------
# Asosiy menyu tugmalari
# ---------------------------------------------------------------------------
@router.message(F.text == "🛒 Buyurtma berish")
async def start_order(message: Message, state: FSMContext):
    await state.set_state(OrderStates.choosing_branch)
    await message.answer("Qaysi filialdan buyurtma bermoqchisiz?", reply_markup=branch_kb())


@router.message(OrderStates.choosing_branch, F.text.in_(BRANCHES))
async def branch_chosen(message: Message, state: FSMContext):
    await state.update_data(branch=message.text)
    await state.set_state(OrderStates.choosing_items)
    await message.answer(
        f"✅ Filial: {message.text}\n\n"
        "Menyudan taomlarni tanlang (bu qismni keyinroq menyu katalogi bilan to'ldiramiz).",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Savatni yakunlash")], [KeyboardButton(text="⬅️ Orqaga")]],
            resize_keyboard=True,
        ),
    )


@router.message(OrderStates.choosing_branch, F.text == "⬅️ Orqaga")
async def branch_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyu:", reply_markup=main_menu_kb())


@router.message(OrderStates.choosing_items, F.text == "✅ Savatni yakunlash")
async def cart_done(message: Message, state: FSMContext):
    await state.set_state(OrderStates.entering_phone)
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=phone_kb())


@router.message(OrderStates.entering_phone, F.contact)
async def phone_received(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(OrderStates.entering_location)
    await message.answer("Yetkazib berish uchun joylashuvingizni yuboring:", reply_markup=location_kb())


@router.message(OrderStates.entering_location, F.location)
async def location_received(message: Message, state: FSMContext):
    data = await state.update_data(
        lat=message.location.latitude, lon=message.location.longitude
    )
    await state.set_state(OrderStates.confirming)

    orders = load_orders()
    orders["order_counter"] += 1
    order_id = orders["order_counter"]
    orders["active_orders"][str(order_id)] = {
        "user_id": message.from_user.id,
        "branch": data.get("branch"),
        "phone": data.get("phone"),
        "location": {"lat": data.get("lat"), "lon": data.get("lon")},
        "status": "yangi",
    }
    save_orders(orders)

    await state.clear()
    await message.answer(
        f"✅ Buyurtmangiz qabul qilindi!\n"
        f"Buyurtma raqami: #{order_id}\n"
        f"Filial: {data.get('branch')}\n\n"
        "Tez orada operator siz bilan bog'lanadi.",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_us(message: Message):
    await message.answer(
        "🥟 Shox Somsa — o'zbek milliy taomlari.\n\n"
        "Bizda: somsa, sushi, salatlar va boshqa milliy taomlar.\n"
        "2 ta filial: Axsikent va Jasmin.",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "🛍 Buyurtmalarim")
async def my_orders(message: Message):
    orders = load_orders()
    user_orders = [
        (oid, o)
        for oid, o in orders["active_orders"].items()
        if o["user_id"] == message.from_user.id
    ]
    if not user_orders:
        await message.answer("Sizda hozircha buyurtmalar yo'q.", reply_markup=main_menu_kb())
        return

    lines = [f"#{oid} — {o['branch']} — {o['status']}" for oid, o in user_orders]
    await message.answer("Sizning buyurtmalaringiz:\n\n" + "\n".join(lines), reply_markup=main_menu_kb())


@router.message(F.text == "🏠 Filiallar")
async def branches_info(message: Message):
    await message.answer(
        "🏠 Filiallarimiz:\n\n"
        "1️⃣ Axsikent\n"
        "2️⃣ Jasmin\n\n"
        "Har ikkala filial ham yetkazib berish xizmatini ko'rsatadi.",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "✍️ Fikr bildirish")
async def feedback_start(message: Message, state: FSMContext):
    await state.set_state(FeedbackStates.waiting_text)
    await message.answer(
        "Fikr va takliflaringizni yozing:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(FeedbackStates.waiting_text)
async def feedback_received(message: Message, state: FSMContext):
    logger.info(f"Feedback from {message.from_user.id}: {message.text}")
    await state.clear()
    await message.answer("Rahmat! Fikringiz qabul qilindi. 🙏", reply_markup=main_menu_kb())


@router.message(F.text == "⚙️ Sozlamalar")
async def settings_menu(message: Message):
    await message.answer(
        "⚙️ Sozlamalar bo'limi tez orada to'ldiriladi.",
        reply_markup=main_menu_kb(),
    )


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------
@router.message()
async def fallback(message: Message):
    await message.answer("Iltimos, menyudan birini tanlang 👇", reply_markup=main_menu_kb())


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
