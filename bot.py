import asyncio
import logging
import os
import aiohttp
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from faker import Faker

# ================== CONFIG ==================
API_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = "PUB-0YLp2Jn3Qbw7qlY4Gu1gPMSR4"

ALLOWED_USERS = {1003539611, 7979473115, 8270778815}
ALLOWED_CHATS = {-1003392192892}

# ================== LOGGING ==================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================== FAKER ==================
fake = Faker()

# ================== CACHE ==================
BIN_CACHE = {}

# ================== FLAG ==================
def country_flag(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🏳️"
    code = country_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))

# ================== API ==================
async def fetch_bin(bin_number: str):
    url = f"https://data.handyapi.com/bin/{bin_number}"
    headers = {"x-api-key": API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            try:
                return await resp.json()
            except:
                return None

# ================== BIN CHECK ==================
async def bin_lookup(bin_number: str) -> str:
    bin_number = ''.join(c for c in bin_number if c.isdigit())

    if len(bin_number) < 6:
        return "❌ Введи минимум 6 цифр."

    bin_number = bin_number[:8]

    if bin_number in BIN_CACHE:
        return BIN_CACHE[bin_number]

    data = await fetch_bin(bin_number)

    if not data:
        return "❌ API не отвечает."

    if data.get("Status") != "SUCCESS":
        return f"❌ Ошибка API: {data}"

    bank = data.get("Issuer", "N/A")
    type_ = data.get("Type", "N/A")
    scheme = data.get("Scheme", "N/A")
    brand = data.get("CardTier", "N/A")

    country_code = data.get("Country", {}).get("A2", "")
    country_name = data.get("Country", {}).get("Name", "N/A")

    flag = country_flag(country_code)

    response = (
        f"<b>Info ⇾</b> <code>{scheme} - {type_} - {brand}</code>\n"
        f"<b>Issuer ⇾</b> <code>{bank}</code>\n"
        f"<b>Country ⇾</b> <code>{country_name}</code> {flag}"
    )

    BIN_CACHE[bin_number] = response
    return response

# ================== FAKE GENERATOR ==================
def generate_fake():
    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"

    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(10,99)}@gmail.com"

    # 🇪🇸 Телефон строго: +34XXXXXXXXX
    phone = f"+34{random.randint(600000000, 799999999)}"

    street = fake.street_address()
    city = fake.city()
    state = fake.state()
    postal_code = fake.postcode()
    country = fake.country()

    return (
        f"<b>Fake Generator</b>\n\n"
        f"Name → <code>{full_name}</code>\n\n"
        f"Street → <code>{street}</code>\n"
        f"City → <code>{city}</code>\n"
        f"State → <code>{state}</code>\n"
        f"ZIP → <code>{postal_code}</code>\n"
        f"Country → <code>{country}</code>\n\n"
        f"Email → <code>{email}</code>\n"
        f"Phone → <code>{phone}</code>"
    )

# ================== START ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "👋 BIN Checker Bot\n\n"
        "Команды:\n"
        "/bin 457173 или !bin 457173\n"
        "/fake или !fake"
    )

# ================== MAIN HANDLER ==================
@dp.message()
async def main_handler(message: types.Message):
    user_id = message.from_user.id

    # 🔒 ЛС
    if message.chat.type == "private":
        if user_id not in ALLOWED_USERS:
            return

    # 🔒 ЧАТЫ
    if message.chat.type in ["group", "supergroup"]:
        if message.chat.id not in ALLOWED_CHATS:
            return

    text = (message.text or "").strip()

    # ===== BIN =====
    if text.startswith("/bin") or text.startswith("!bin"):
        args = text[4:].strip()

        if not args:
            await message.answer("❌ Пример: /bin 457173")
            return

        response = await bin_lookup(args)
        await message.answer(response, parse_mode="HTML")
        return

    # ===== FAKE =====
    if text.startswith("/fake") or text.startswith("!fake"):
        data = generate_fake()
        await message.answer(data, parse_mode="HTML")
        return

# ================== RUN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
