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

BRANCHES = [
    "Andijon",
    "Buxoro",
    "Farg'ona",
    "Jizzax",
    "Namangan",
    "Navoiy",
    "Qashqadaryo",
    "Samarqand",
    "Sirdaryo",
    "Surxondaryo",
    "Toshkent viloyati",
    "Xorazm",
]

# ---------------------------------------------------------------------------
# Menyu: kategoriyalar va taomlar (narxlar so'mda)
# ---------------------------------------------------------------------------
MENU = {
    "🍚 Milliy taomlar": [
        {"name": "Osh (Palov)", "price": 25000},
        {"name": "Lag'mon", "price": 22000},
        {"name": "Manti", "price": 20000},
        {"name": "Norin", "price": 24000},
        {"name": "Dimlama", "price": 26000},
        {"name": "Mastava", "price": 18000},
        {"name": "Chuchvara", "price": 20000},
        {"name": "Shashlik (qo'y go'shti)", "price": 32000},
        {"name": "Shashlik (tovuq)", "price": 24000},
    ],
    "🥟 Somsa": [
        {"name": "Go'shtli somsa", "price": 8000},
        {"name": "Kartoshkali somsa", "price": 6000},
        {"name": "Tovuqli somsa", "price": 7000},
        {"name": "Qovoqli somsa", "price": 7000},
    ],
    "🥗 Salatlar": [
        {"name": "Achchiq-chuchuk salat", "price": 10000},
        {"name": "Vinegret", "price": 12000},
        {"name": "Sezar salat", "price": 18000},
        {"name": "Ko'k salat", "price": 8000},
    ],
    "🥤 Ichimliklar": [
        {"name": "Choy (choynak)", "price": 4000},
        {"name": "Kompot", "price": 6000},
        {"name": "Kola 0.5L", "price": 8000},
        {"name": "Mineral suv", "price": 4000},
    ],
    "🍞 Non va boshqalar": [
        {"name": "Non", "price": 4000},
        {"name": "Ayron", "price": 5000},
    ],
}

# Aksiya taomlari (chegirmali narx bilan)
AKSIYA = [
    {
        "name": "🔥 Osh + Choy seti",
        "price": 22000,
        "old_price": 29000,
    },
    {
        "name": "🔥 Shashlik seti (3 tayoq + non + salat)",
        "price": 48000,
        "old_price": 62000,
    },
    {
        "name": "🔥 Lag'mon + Ayron",
        "price": 24000,
        "old_price": 30000,
    },
    {
        "name": "🔥 Somsa 5 dona (aralash)",
        "price": 30000,
        "old_price": 38000,
    },
]

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


def find_item(name: str):
    """Nomi bo'yicha menyu yoki aksiyadan taomni topish."""
    for items in MENU.values():
        for item in items:
            if item["name"] == name:
                return item
    for item in AKSIYA:
        if item["name"] == name:
            return {"name": item["name"], "price": item["price"]}
    return None


def format_cart(cart: list) -> str:
    if not cart:
        return "Savatingiz bo'sh."
    lines = []
    total = 0
    for entry in cart:
        subtotal = entry["price"] * entry["qty"]
        total += subtotal
        lines.append(f"• {entry['name']} x{entry['qty']} — {subtotal:,} so'm".replace(",", " "))
    lines.append(f"\n💰 Jami: {total:,} so'm".replace(",", " "))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# FSM holatlar
# ---------------------------------------------------------------------------
class OrderStates(StatesGroup):
    choosing_branch = State()
    choosing_category = State()
    choosing_item = State()
    entering_quantity = State()
    cart_review = State()
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
            [KeyboardButton(text="🔥 Aksiyalar")],
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
    rows = [
        [KeyboardButton(text=BRANCHES[i]), KeyboardButton(text=BRANCHES[i + 1])]
        if i + 1 < len(BRANCHES)
        else [KeyboardButton(text=BRANCHES[i])]
        for i in range(0, len(BRANCHES), 2)
    ]
    rows.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def category_kb() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=cat)] for cat in MENU.keys()]
    rows.append([KeyboardButton(text="🔥 Aksiyalar")])
    rows.append([KeyboardButton(text="✅ Savatni yakunlash")])
    rows.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def items_kb(category: str) -> ReplyKeyboardMarkup:
    items = MENU.get(category, [])
    rows = [[KeyboardButton(text=item["name"])] for item in items]
    rows.append([KeyboardButton(text="⬅️ Kategoriyalarga qaytish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def aksiya_kb() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=item["name"])] for item in AKSIYA]
    rows.append([KeyboardButton(text="⬅️ Kategoriyalarga qaytish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def quantity_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
            [KeyboardButton(text="4"), KeyboardButton(text="5")],
            [KeyboardButton(text="⬅️ Bekor qilish")],
        ],
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
        "Restoran botimizga xush kelibsiz.\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=main_menu_kb(),
    )


# ---------------------------------------------------------------------------
# Aksiyalarni ko'rsatish (bosh menyudan)
# ---------------------------------------------------------------------------
@router.message(F.text == "🔥 Aksiyalar")
async def aksiya_info(message: Message):
    lines = []
    for item in AKSIYA:
        lines.append(
            f"🔥 {item['name']}\n"
            f"   ~~{item['old_price']:,} so'm~~ → {item['price']:,} so'm".replace(",", " ")
        )
    await message.answer(
        "Joriy aksiyalar:\n\n" + "\n\n".join(lines) + "\n\nBuyurtma berish uchun 🛒 tugmasini bosing.",
        reply_markup=main_menu_kb(),
    )


# ---------------------------------------------------------------------------
# Buyurtma jarayoni
# ---------------------------------------------------------------------------
@router.message(F.text == "🛒 Buyurtma berish")
async def start_order(message: Message, state: FSMContext):
    await state.set_state(OrderStates.choosing_branch)
    await state.update_data(cart=[])
    await message.answer("Qaysi viloyatga yetkazib berish kerak?", reply_markup=branch_kb())


@router.message(OrderStates.choosing_branch, F.text.in_(BRANCHES))
async def branch_chosen(message: Message, state: FSMContext):
    await state.update_data(branch=message.text)
    await state.set_state(OrderStates.choosing_category)
    await message.answer(
        f"✅ Viloyat: {message.text}\n\nKategoriyani tanlang:",
        reply_markup=category_kb(),
    )


@router.message(OrderStates.choosing_branch, F.text == "⬅️ Orqaga")
async def branch_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyu:", reply_markup=main_menu_kb())


@router.message(OrderStates.choosing_category, F.text.in_(list(MENU.keys())))
async def category_chosen(message: Message, state: FSMContext):
    await state.update_data(current_category=message.text)
    await state.set_state(OrderStates.choosing_item)
    await message.answer(
        f"{message.text} bo'limi:",
        reply_markup=items_kb(message.text),
    )


@router.message(OrderStates.choosing_category, F.text == "🔥 Aksiyalar")
async def category_aksiya(message: Message, state: FSMContext):
    lines = []
    for item in AKSIYA:
        lines.append(
            f"🔥 {item['name']}\n"
            f"   ~~{item['old_price']:,} so'm~~ → {item['price']:,} so'm".replace(",", " ")
        )
    await state.update_data(current_category="__aksiya__")
    await state.set_state(OrderStates.choosing_item)
    await message.answer(
        "Aksiya taomlari:\n\n" + "\n\n".join(lines),
        reply_markup=aksiya_kb(),
    )


@router.message(OrderStates.choosing_category, F.text == "✅ Savatni yakunlash")
async def cart_done_from_category(message: Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", [])
    if not cart:
        await message.answer("Savatingiz bo'sh. Avval taom tanlang.", reply_markup=category_kb())
        return
    await state.set_state(OrderStates.cart_review)
    await message.answer(
        "🧾 Savatingiz:\n\n" + format_cart(cart),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Buyurtmani tasdiqlash")],
                [KeyboardButton(text="➕ Yana taom qo'shish")],
            ],
            resize_keyboard=True,
        ),
    )


@router.message(OrderStates.choosing_category, F.text == "⬅️ Orqaga")
async def category_back(message: Message, state: FSMContext):
    await state.set_state(OrderStates.choosing_branch)
    await message.answer("Qaysi viloyatga yetkazib berish kerak?", reply_markup=branch_kb())


@router.message(OrderStates.choosing_item, F.text == "⬅️ Kategoriyalarga qaytish")
async def item_back(message: Message, state: FSMContext):
    await state.set_state(OrderStates.choosing_category)
    await message.answer("Kategoriyani tanlang:", reply_markup=category_kb())


@router.message(OrderStates.choosing_item)
async def item_chosen(message: Message, state: FSMContext):
    item = find_item(message.text)
    if not item:
        await message.answer("Iltimos, ro'yxatdan taom tanlang 👇")
        return
    await state.update_data(pending_item=item)
    await state.set_state(OrderStates.entering_quantity)
    await message.answer(f"{item['name']} — nechta dona?", reply_markup=quantity_kb())


@router.message(OrderStates.entering_quantity, F.text == "⬅️ Bekor qilish")
async def quantity_cancel(message: Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("current_category")
    await state.set_state(OrderStates.choosing_item)
    if category == "__aksiya__":
        await message.answer("Bekor qilindi.", reply_markup=aksiya_kb())
    else:
        await message.answer("Bekor qilindi.", reply_markup=items_kb(category))


@router.message(OrderStates.entering_quantity, F.text.regexp(r"^\d+$"))
async def quantity_entered(message: Message, state: FSMContext):
    qty = int(message.text)
    if qty <= 0 or qty > 50:
        await message.answer("Iltimos, 1 dan 50 gacha son kiriting.")
        return

    data = await state.get_data()
    item = data.get("pending_item")
    cart = data.get("cart", [])

    for entry in cart:
        if entry["name"] == item["name"]:
            entry["qty"] += qty
            break
    else:
        cart.append({"name": item["name"], "price": item["price"], "qty": qty})

    await state.update_data(cart=cart)
    category = data.get("current_category")
    await state.set_state(OrderStates.choosing_category)
    await message.answer(
        f"✅ {item['name']} x{qty} savatga qo'shildi.\n\n" + format_cart(cart),
        reply_markup=category_kb(),
    )


@router.message(OrderStates.cart_review, F.text == "➕ Yana taom qo'shish")
async def cart_add_more(message: Message, state: FSMContext):
    await state.set_state(OrderStates.choosing_category)
    await message.answer("Kategoriyani tanlang:", reply_markup=category_kb())


@router.message(OrderStates.cart_review, F.text == "✅ Buyurtmani tasdiqlash")
async def cart_confirm(message: Message, state: FSMContext):
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

    cart = data.get("cart", [])
    total = sum(e["price"] * e["qty"] for e in cart)

    orders = load_orders()
    orders["order_counter"] += 1
    order_id = orders["order_counter"]
    orders["active_orders"][str(order_id)] = {
        "user_id": message.from_user.id,
        "region": data.get("branch"),
        "phone": data.get("phone"),
        "location": {"lat": data.get("lat"), "lon": data.get("lon")},
        "cart": cart,
        "total": total,
        "status": "yangi",
    }
    save_orders(orders)

    await state.clear()
    await message.answer(
        f"✅ Buyurtmangiz qabul qilindi!\n"
        f"Buyurtma raqami: #{order_id}\n"
        f"Viloyat: {data.get('branch')}\n\n"
        f"{format_cart(cart)}\n\n"
        "Tez orada operator siz bilan bog'lanadi.",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_us(message: Message):
    await message.answer(
        "🥟 Restoranimiz — o'zbek milliy taomlari.\n\n"
        "Bizda: milliy taomlar, somsa, sushi, salatlar va ichimliklar.\n"
        "O'zbekistonning 12 ta viloyatiga yetkazib beramiz.",
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

    lines = [
        f"#{oid} — {o['region']} — {o.get('total', 0):,} so'm — {o['status']}".replace(",", " ")
        for oid, o in user_orders
    ]
    await message.answer("Sizning buyurtmalaringiz:\n\n" + "\n".join(lines), reply_markup=main_menu_kb())


@router.message(F.text == "🏠 Filiallar")
async def branches_info(message: Message):
    lines = "\n".join(f"{i+1}. {b}" for i, b in enumerate(BRANCHES))
    await message.answer(
        "🏠 Yetkazib berish hududlarimiz:\n\n"
        f"{lines}\n\n"
        "Barcha viloyatlarga yetkazib berish xizmati mavjud.",
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
