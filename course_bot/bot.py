# Kurs markazi uchun Telegram bot (aiogram 3.x)
# Bo'limlar: Buyurtma berish (savat), Aksiyalar, Joy band qilish, Filiallar,
#            Fikr bildirish, Biz haqimizda
# O'rnatish: pip install aiogram

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)

# ====================== SOZLAMALAR ======================
BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ====================== MA'LUMOTLAR ======================

FILIALLAR = {
    "andijon": {"nomi": "Andijon filiali", "manzil": "Andijon sh., Bobur ko'chasi 12", "tel": "+998 90 000 00 01"},
    "buxoro": {"nomi": "Buxoro filiali", "manzil": "Buxoro sh., Mustaqillik ko'chasi 5", "tel": "+998 90 000 00 02"},
    "fargona": {"nomi": "Farg'ona filiali", "manzil": "Farg'ona sh., Al-Farg'oniy ko'chasi 8", "tel": "+998 90 000 00 03"},
    "jizzax": {"nomi": "Jizzax filiali", "manzil": "Jizzax sh., Sharof Rashidov ko'chasi 3", "tel": "+998 90 000 00 04"},
    "xorazm": {"nomi": "Xorazm filiali", "manzil": "Urganch sh., Al-Xorazmiy ko'chasi 15", "tel": "+998 90 000 00 05"},
    "namangan": {"nomi": "Namangan filiali", "manzil": "Namangan sh., Uychi ko'chasi 22", "tel": "+998 90 000 00 06"},
    "navoiy": {"nomi": "Navoiy filiali", "manzil": "Navoiy sh., Alisher Navoiy ko'chasi 9", "tel": "+998 90 000 00 07"},
    "qashqadaryo": {"nomi": "Qashqadaryo filiali", "manzil": "Qarshi sh., Mustaqillik ko'chasi 30", "tel": "+998 90 000 00 08"},
    "samarqand": {"nomi": "Samarqand filiali", "manzil": "Samarqand sh., Registon ko'chasi 1", "tel": "+998 90 000 00 09"},
    "sirdaryo": {"nomi": "Sirdaryo filiali", "manzil": "Guliston sh., Bunyodkor ko'chasi 4", "tel": "+998 90 000 00 10"},
    "surxondaryo": {"nomi": "Surxondaryo filiali", "manzil": "Termiz sh., Alpomish ko'chasi 6", "tel": "+998 90 000 00 11"},
    "toshkent": {"nomi": "Toshkent filiali", "manzil": "Toshkent sh., Amir Temur shoh ko'chasi 1", "tel": "+998 90 000 00 12"},
}

COURSES = {
    "smm": {
        "name": "📊 SMM asoslari",
        "muddat": "4 hafta",
        "dastur": [
            "Ijtimoiy tarmoqlar algoritmlari va kontent strategiyasi",
            "Instagram, Telegram, Facebook uchun kontent-reja tuzish",
            "Fotosurat va video montaj asoslari (Reels/Shorts)",
            "Target reklama sozlash va byudjetni boshqarish",
            "Statistika tahlili va natijalarni oshirish",
            "Brend uchun kontent-plan va yakuniy loyiha himoyasi",
        ],
        "tariffs": {
            "standard": {"name": "Standart", "price": 250000},
            "premium": {"name": "Premium (1:1 mentor bilan)", "price": 450000},
        },
    },
    "python": {
        "name": "💻 Python dasturlash",
        "muddat": "8 hafta",
        "dastur": [
            "Python sintaksisi, o'zgaruvchilar, shartli operatorlar",
            "Funksiyalar, ro'yxatlar, lug'atlar, tsikllar",
            "Fayllar bilan ishlash va xatoliklarni boshqarish (try/except)",
            "OOP (obyektga yo'naltirilgan dasturlash) asoslari",
            "Ma'lumotlar bazasi bilan ishlash (SQLite)",
            "Amaliy loyiha: web-sayt yoki Telegram bot yaratish",
        ],
        "tariffs": {
            "standard": {"name": "Standart", "price": 400000},
            "premium": {"name": "Premium (portfolio loyihasi bilan)", "price": 700000},
        },
    },
    "freelance": {
        "name": "📈 Frilanser bo'lish",
        "muddat": "3 hafta",
        "dastur": [
            "Frilans platformalarni tanlash (Upwork, Fiverr, Freelancer)",
            "Kuchli profil va portfolio yaratish",
            "Mijoz bilan muzokara va narx belgilash",
            "Birinchi buyurtmani topish strategiyalari",
            "To'lovlarni qabul qilish va soliq masalalari",
        ],
        "tariffs": {
            "standard": {"name": "Standart", "price": 200000},
            "premium": {"name": "Premium (amaliy nazorat bilan)", "price": 350000},
        },
    },
    "english": {
        "name": "🇬🇧 Ingliz tili",
        "muddat": "12 hafta",
        "dastur": [
            "Grammatika asoslari va so'z boyligini oshirish",
            "Speaking club: erkin muloqot mashqlari",
            "Listening: filmlar va podkastlar orqali tinglab tushunish",
            "Writing: esse va rasmiy xat yozish",
            "IELTS/CEFR formatidagi test topshiriqlari",
        ],
        "tariffs": {
            "standard": {"name": "Standart (guruh)", "price": 300000},
            "premium": {"name": "Premium (individual dars)", "price": 550000},
        },
    },
    "math": {
        "name": "➗ Matematika",
        "muddat": "10 hafta",
        "dastur": [
            "Algebra va tenglamalar",
            "Geometriya asoslari",
            "Funksiyalar va grafiklar",
            "Test topshirish strategiyalari (DTM/Milliy sertifikat)",
            "Mantiqiy fikrlash va masala yechish mashqlari",
        ],
        "tariffs": {
            "standard": {"name": "Standart (guruh)", "price": 280000},
            "premium": {"name": "Premium (individual dars)", "price": 500000},
        },
    },
    "computer_literacy": {
        "name": "🖥 Kompyuter savodxonligi",
        "muddat": "3 hafta",
        "dastur": [
            "Windows va fayllar bilan ishlash asoslari",
            "MS Word, Excel, PowerPoint dasturlari",
            "Internetdan xavfsiz foydalanish va elektron pochta",
            "Onlayn davlat xizmatlaridan foydalanish (my.gov.uz va h.k.)",
        ],
        "tariffs": {
            "standard": {"name": "Standart", "price": 150000},
            "premium": {"name": "Premium (tezlashtirilgan)", "price": 250000},
        },
    },
    "webdesign": {
        "name": "🎨 Web dizayn",
        "muddat": "6 hafta",
        "dastur": [
            "HTML va CSS asoslari",
            "Figma'da interfeys (UI/UX) loyihalash",
            "Responsive (moslashuvchan) dizayn tamoyillari",
            "Tayyor dizaynni web-sahifaga aylantirish",
            "Portfolio uchun 2 ta amaliy loyiha",
        ],
        "tariffs": {
            "standard": {"name": "Standart", "price": 350000},
            "premium": {"name": "Premium (portfolio bilan)", "price": 600000},
        },
    },
    "mobile_dev": {
        "name": "📱 Mobil dasturlash",
        "muddat": "10 hafta",
        "dastur": [
            "Dart tili va Flutter asoslari",
            "UI komponentlar va navigatsiya",
            "API bilan ishlash va ma'lumotlarni saqlash",
            "Ilovani Play Market/App Store uchun tayyorlash",
            "Amaliy loyiha: to'liq mobil ilova yaratish",
        ],
        "tariffs": {
            "standard": {"name": "Standart", "price": 500000},
            "premium": {"name": "Premium (portfolio loyihasi bilan)", "price": 850000},
        },
    },
    "data_analytics": {
        "name": "📊 Data Analiz",
        "muddat": "8 hafta",
        "dastur": [
            "Excel va Google Sheets orqali ma'lumotlar tahlili",
            "SQL asoslari va ma'lumotlar bazasidan so'rov yozish",
            "Python (pandas) yordamida tahlil",
            "Ma'lumotlarni vizualizatsiya qilish (dashboard yaratish)",
            "Amaliy loyiha: real ma'lumotlar asosida hisobot tayyorlash",
        ],
        "tariffs": {
            "standard": {"name": "Standart", "price": 400000},
            "premium": {"name": "Premium (mentor bilan)", "price": 700000},
        },
    },
}

# Aksiyadagi kurslar: chegirmali narx (bitta tarif bo'yicha, bir bosishda savatga qo'shiladi)
PROMOTIONS = {
    "smm": {"tariff": "standard", "old_price": 250000, "price": 180000},
    "python": {"tariff": "standard", "old_price": 400000, "price": 320000},
}

BIZ_HAQIMIZDA = (
    "ℹ️ <b>Biz haqimizda</b>\n\n"
    "Biz — amaliy ko'nikmalarga asoslangan onlayn va oflayn kurslar markazimiz. "
    "SMM, Python dasturlash va frilanserlik bo'yicha 3 yildan ortiq tajribaga ega "
    "o'qituvchilar bilan ishlaymiz.\n\n"
    "12 ta viloyatda filiallarimiz mavjud, shuning uchun qayerda bo'lishingizdan "
    "qat'i nazar bizning kurslarimizga qatnashishingiz mumkin.\n\n"
    "Savollaringiz bo'lsa, \"✍️ Fikr bildirish\" bo'limi orqali biz bilan bog'lanishingiz mumkin."
)

# Kunlik vaqt oralig'i: 08:00 dan 01:00 gacha, har biri 2 soatlik slot
def build_time_slots():
    slots = []
    start_minutes = 8 * 60
    end_minutes = 25 * 60  # 01:00 (keyingi kun)
    step = 2 * 60
    cur = start_minutes
    while cur < end_minutes:
        nxt = min(cur + step, end_minutes)
        start_h, start_m = (cur // 60) % 24, cur % 60
        end_h, end_m = (nxt // 60) % 24, nxt % 60
        slots.append(f"{start_h:02d}:{start_m:02d}–{end_h:02d}:{end_m:02d}")
        cur = nxt
    return slots

TIME_SLOTS = build_time_slots()

# ====================== HOLATLAR (FSM) ======================

class Order(StatesGroup):
    choosing_branch = State()
    entering_name = State()
    entering_phone = State()


class Booking(StatesGroup):
    choosing_branch = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State()


class Feedback(StatesGroup):
    entering_text = State()


# ====================== XOTIRADAGI MA'LUMOTLAR ======================

carts: dict[int, list[dict]] = {}          # user_id -> [{course_key, tariff_key, tariff_name, price}]
booking_data: dict[int, dict] = {}         # user_id -> {branch_key, time_slot}

# ====================== KLAVIATURALAR ======================

MAIN_MENU = [
    ["🛒 Buyurtma berish", "🔥 Aksiyalar"],
    ["📅 Joy band qilish", "🏠 Filiallar"],
    ["✍️ Fikr bildirish", "ℹ️ Biz haqimizda"],
]


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in MAIN_MENU],
        resize_keyboard=True,
    )


def phone_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def categories_kb() -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text=info["name"], callback_data=f"cat:{key}")] for key, info in COURSES.items()]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def tariffs_kb(course_key: str) -> InlineKeyboardMarkup:
    info = COURSES[course_key]
    kb = []
    for t_key, t_info in info["tariffs"].items():
        kb.append([InlineKeyboardButton(
            text=f"{t_info['name']} — {t_info['price']:,} so'm".replace(",", " "),
            callback_data=f"tariff:{course_key}:{t_key}",
        )])
    kb.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="cat:back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def cart_view_kb() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="➕ Yana kurs qo'shish", callback_data="cart:add_more")],
        [InlineKeyboardButton(text="✅ Buyurtmani rasmiylashtirish", callback_data="cart:checkout")],
        [InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="cart:clear")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def promotions_kb() -> InlineKeyboardMarkup:
    kb = []
    for key, promo in PROMOTIONS.items():
        name = COURSES[key]["name"]
        kb.append([InlineKeyboardButton(
            text=f"{name} — {promo['price']:,} so'm (avval {promo['old_price']:,})".replace(",", " "),
            callback_data=f"promo:{key}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def branches_kb(prefix: str) -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text=info["nomi"], callback_data=f"{prefix}:{key}")] for key, info in FILIALLAR.items()]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def time_slots_kb() -> InlineKeyboardMarkup:
    kb = []
    row = []
    for i, slot in enumerate(TIME_SLOTS, start=1):
        row.append(InlineKeyboardButton(text=slot, callback_data=f"book_time:{slot}"))
        if i % 2 == 0:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ====================== YORDAMCHI FUNKSIYALAR ======================

def format_cart(user_id: int) -> str:
    items = carts.get(user_id, [])
    if not items:
        return "🛒 Savatingiz bo'sh."
    lines = ["🛒 <b>Savatingiz:</b>\n"]
    total = 0
    for i, item in enumerate(items, start=1):
        course_name = COURSES[item["course_key"]]["name"]
        lines.append(f"{i}. {course_name} — {item['tariff_name']} — {item['price']:,} so'm".replace(",", " "))
        total += item["price"]
    lines.append(f"\n<b>Jami: {total:,} so'm</b>".replace(",", " "))
    return "\n".join(lines)


def format_course_details(course_key: str) -> str:
    info = COURSES[course_key]
    dastur_lines = "\n".join(f"• {topic}" for topic in info["dastur"])
    return (
        f"<b>{info['name']}</b>\n"
        f"⏳ Muddati: {info['muddat']}\n\n"
        f"<b>Kursda nimalar o'rgatiladi:</b>\n{dastur_lines}\n\n"
        f"Quyidagi tariflardan birini tanlang:"
    )


# ====================== ASOSIY MENYU ======================

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    carts.pop(message.from_user.id, None)
    await message.answer(
        "Assalomu alaykum! 🎓 Kurs markazimizga xush kelibsiz.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu_kb(),
    )


# ---------- 🛒 Buyurtma berish ----------

@router.message(F.text == "🛒 Buyurtma berish")
async def order_start(message: Message, state: FSMContext):
    await message.answer("Quyidagi kurslardan birini tanlang:", reply_markup=categories_kb())


@router.callback_query(F.data.startswith("cat:"))
async def show_category(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    if key == "back":
        await callback.message.edit_text("Quyidagi kurslardan birini tanlang:", reply_markup=categories_kb())
        await callback.answer()
        return
    await callback.message.edit_text(format_course_details(key), reply_markup=tariffs_kb(key), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("tariff:"))
async def add_tariff_to_cart(callback: CallbackQuery):
    _, course_key, tariff_key = callback.data.split(":")
    user_id = callback.from_user.id
    tariff = COURSES[course_key]["tariffs"][tariff_key]
    carts.setdefault(user_id, []).append({
        "course_key": course_key,
        "tariff_key": tariff_key,
        "tariff_name": tariff["name"],
        "price": tariff["price"],
    })
    await callback.message.edit_text(
        f"✅ \"{COURSES[course_key]['name']}\" ({tariff['name']}) savatga qo'shildi!\n\n{format_cart(user_id)}",
        reply_markup=cart_view_kb(),
        parse_mode="HTML",
    )
    await callback.answer("Savatga qo'shildi")


@router.callback_query(F.data == "cart:add_more")
async def cart_add_more(callback: CallbackQuery):
    await callback.message.edit_text("Quyidagi kurslardan birini tanlang:", reply_markup=categories_kb())
    await callback.answer()


@router.callback_query(F.data == "cart:clear")
async def cart_clear(callback: CallbackQuery):
    carts.pop(callback.from_user.id, None)
    await callback.message.edit_text("🗑 Savat tozalandi.", reply_markup=None)
    await callback.answer()


@router.callback_query(F.data == "cart:checkout")
async def cart_checkout(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not carts.get(user_id):
        await callback.answer("Savatingiz bo'sh!", show_alert=True)
        return
    await callback.message.answer("Qaysi filialdan xarid qilmoqchisiz?", reply_markup=branches_kb("order_branch"))
    await state.set_state(Order.choosing_branch)
    await callback.answer()


@router.callback_query(Order.choosing_branch, F.data.startswith("order_branch:"))
async def order_branch_chosen(callback: CallbackQuery, state: FSMContext):
    branch_key = callback.data.split(":", 1)[1]
    await state.update_data(branch_key=branch_key)
    await callback.message.answer("Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Order.entering_name)
    await callback.answer()


@router.message(Order.entering_name)
async def order_name_entered(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer(
        "Telefon raqamingizni yuboring (tugma orqali yoki qo'lda kiriting):",
        reply_markup=phone_request_kb(),
    )
    await state.set_state(Order.entering_phone)


@router.message(Order.entering_phone)
async def order_phone_entered(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    user_id = message.from_user.id
    cart_text = format_cart(user_id)
    branch_name = FILIALLAR[data["branch_key"]]["nomi"]

    await message.answer(
        f"✅ Buyurtmangiz qabul qilindi!\n\n"
        f"{cart_text}\n\n"
        f"🏠 Filial: {branch_name}\n"
        f"👤 Ism: {data['full_name']}\n"
        f"📞 Telefon: {phone}\n\n"
        f"Tez orada operatorlarimiz siz bilan bog'lanadi.",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )

    if ADMIN_CHAT_ID:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"🆕 Yangi buyurtma!\n\n"
            f"{cart_text}\n\n"
            f"🏠 Filial: {branch_name}\n"
            f"👤 Ism: {data['full_name']}\n"
            f"📞 Telefon: {phone}\n"
            f"🆔 Mijoz: @{message.from_user.username or user_id} (ID: {user_id})",
            parse_mode="HTML",
        )

    carts.pop(user_id, None)
    await state.clear()


# ---------- 🔥 Aksiyalar ----------

@router.message(F.text == "🔥 Aksiyalar")
async def promotions_start(message: Message):
    if not PROMOTIONS:
        await message.answer("Hozircha aksiyalar mavjud emas.")
        return
    await message.answer("🔥 Aksiyadagi kurslar:", reply_markup=promotions_kb())


@router.callback_query(F.data.startswith("promo:"))
async def add_promo_to_cart(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    promo = PROMOTIONS[key]
    tariff_name = COURSES[key]["tariffs"][promo["tariff"]]["name"]
    user_id = callback.from_user.id
    carts.setdefault(user_id, []).append({
        "course_key": key,
        "tariff_key": promo["tariff"],
        "tariff_name": f"{tariff_name} (aksiya)",
        "price": promo["price"],
    })
    await callback.message.edit_text(
        f"✅ \"{COURSES[key]['name']}\" chegirmali narxda savatga qo'shildi!\n\n{format_cart(user_id)}",
        reply_markup=cart_view_kb(),
        parse_mode="HTML",
    )
    await callback.answer("Savatga qo'shildi")


# ---------- 📅 Joy band qilish ----------

@router.message(F.text == "📅 Joy band qilish")
async def booking_start(message: Message, state: FSMContext):
    await message.answer("Qaysi filialdan joy band qilmoqchisiz?", reply_markup=branches_kb("book_branch"))
    await state.set_state(Booking.choosing_branch)


@router.callback_query(Booking.choosing_branch, F.data.startswith("book_branch:"))
async def booking_branch_chosen(callback: CallbackQuery, state: FSMContext):
    branch_key = callback.data.split(":", 1)[1]
    await state.update_data(branch_key=branch_key)
    await callback.message.edit_text(
        f"{FILIALLAR[branch_key]['nomi']} tanlandi.\nEndi qulay vaqtni tanlang (har bir dars 2 soat):",
    )
    await callback.message.answer("Vaqtni tanlang:", reply_markup=time_slots_kb())
    await state.set_state(Booking.choosing_time)
    await callback.answer()


@router.callback_query(Booking.choosing_time, F.data.startswith("book_time:"))
async def booking_time_chosen(callback: CallbackQuery, state: FSMContext):
    time_slot = callback.data.split(":", 1)[1]
    await state.update_data(time_slot=time_slot)
    await callback.message.answer("Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Booking.entering_name)
    await callback.answer()


@router.message(Booking.entering_name)
async def booking_name_entered(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer(
        "Telefon raqamingizni yuboring (tugma orqali yoki qo'lda kiriting):",
        reply_markup=phone_request_kb(),
    )
    await state.set_state(Booking.entering_phone)


@router.message(Booking.entering_phone)
async def booking_phone_entered(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    user_id = message.from_user.id
    branch = FILIALLAR[data["branch_key"]]

    await message.answer(
        f"✅ Joyingiz band qilindi!\n\n"
        f"🏠 Filial: {branch['nomi']}\n"
        f"🕒 Vaqt: {data['time_slot']}\n"
        f"👤 Ism: {data['full_name']}\n"
        f"📞 Telefon: {phone}\n\n"
        f"Tasdiqlash uchun operatorlarimiz siz bilan bog'lanadi.",
        reply_markup=main_menu_kb(),
    )

    if ADMIN_CHAT_ID:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"🆕 Yangi joy band qilish!\n\n"
            f"🏠 Filial: {branch['nomi']}\n"
            f"🕒 Vaqt: {data['time_slot']}\n"
            f"👤 Ism: {data['full_name']}\n"
            f"📞 Telefon: {phone}\n"
            f"🆔 Mijoz: @{message.from_user.username or user_id} (ID: {user_id})",
        )

    await state.clear()


# ---------- 🏠 Filiallar ----------

@router.message(F.text == "🏠 Filiallar")
async def show_branches(message: Message):
    lines = ["🏠 <b>Filiallarimiz (12 viloyatda):</b>\n"]
    for info in FILIALLAR.values():
        lines.append(f"• <b>{info['nomi']}</b>\n  📍 {info['manzil']}\n  📞 {info['tel']}")
    await message.answer("\n\n".join(lines), parse_mode="HTML")


# ---------- ✍️ Fikr bildirish ----------

@router.message(F.text == "✍️ Fikr bildirish")
async def feedback_start(message: Message, state: FSMContext):
    await message.answer(
        "Fikr, taklif yoki shikoyatingizni yozib qoldiring, biz albatta o'qib chiqamiz:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(Feedback.entering_text)


@router.message(Feedback.entering_text)
async def feedback_received(message: Message, state: FSMContext):
    await message.answer("Fikringiz uchun rahmat! ✅", reply_markup=main_menu_kb())
    if ADMIN_CHAT_ID:
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"✍️ Yangi fikr:\n\n{message.text}\n\n"
            f"🆔 Mijoz: @{message.from_user.username or message.from_user.id} (ID: {message.from_user.id})",
        )
    await state.clear()


# ---------- ℹ️ Biz haqimizda ----------

@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_us(message: Message):
    await message.answer(BIZ_HAQIMIZDA, parse_mode="HTML")


# ====================== ISHGA TUSHIRISH ======================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
