import asyncio
import logging
import os
import aiohttp
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from faker import Faker
from faker.config import AVAILABLE_LOCALES

# ================== CONFIG ==================
API_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = "PUB-0YLp2Jn3Qbw7qlY4Gu1gPMSR4"

ALLOWED_USERS = {8270778815,7979473115,1003539611,8412856341}
ALLOWED_CHATS = {-1003392192892}

# ================== LOGGING ==================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================== CACHE ==================
BIN_CACHE = {}

# ================== FLAG ==================
def country_flag(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🏳️"
    code = country_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))

# ================== FAKE ==================
async def fake_generator(country: str) -> str:
    country = country.lower()

    # 🔥 авто-поиск локали
    locale = None
    for loc in AVAILABLE_LOCALES:
        if country in loc.lower():
            locale = loc
            break

    if not locale:
        locale = "en_US"

    fake = Faker(locale)

    name = fake.name()
    street = fake.street_address()
    city = fake.city()

    try:
        state = fake.state()
    except:
        state = "N/A"

    try:
        zip_code = fake.postcode()
    except:
        zip_code = "N/A"

    try:
        country_name = fake.current_country()
    except:
        country_name = locale

    # 🌍 код страны
    prefix = locale.split("_")[-1]

    phone_codes = {
        "US": "1", "GB": "44", "FR": "33", "DE": "49", "ES": "34",
        "IT": "39", "NL": "31", "BE": "32", "CH": "41", "AT": "43",
        "PL": "48", "CZ": "420", "SK": "421", "HU": "36", "RO": "40",
        "BG": "359", "GR": "30", "PT": "351", "SE": "46", "NO": "47",
        "FI": "358", "DK": "45", "EE": "372", "LV": "371", "LT": "370",
        "UA": "380", "RU": "7", "RS": "381",

        "CA": "1", "MX": "52", "BR": "55", "AR": "54", "CL": "56",
        "CO": "57", "PE": "51", "VE": "58",

        "CN": "86", "JP": "81", "KR": "82", "IN": "91", "ID": "62",
        "TH": "66", "VN": "84", "PH": "63", "MY": "60", "SG": "65",

        "TR": "90", "AE": "971", "SA": "966", "IL": "972",

        "ZA": "27", "EG": "20", "NG": "234", "KE": "254", "MA": "212",

        "AU": "61", "NZ": "64"
    }

    code = phone_codes.get(prefix, "1")
    local_number = ''.join(str(random.randint(0, 9)) for _ in range(9))
    phone = f"+{code}{local_number}"

    email = fake.email()

    return (
        f"<b>Fake Generator</b>\n\n"
        f"<b>Name ⇾</b> <code>{name}</code>\n\n"
        f"<b>Street ⇾</b> <code>{street}</code>\n"
        f"<b>City ⇾</b> <code>{city}</code>\n"
        f"<b>State ⇾</b> <code>{state}</code>\n"
        f"<b>ZIP ⇾</b> <code>{zip_code}</code>\n"
        f"<b>Country ⇾</b> <code>{country_name}</code>\n\n"
        f"<b>Email ⇾</b> <code>{email}</code>\n"
        f"<b>Phone ⇾</b> <code>{phone}</code>"
    )

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

# ================== BIN ==================
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

    return (
        f"<b>Info ⇾</b> <code>{scheme} - {type_} - {brand}</code>\n"
        f"<b>Issuer ⇾</b> <code>{bank}</code>\n"
        f"<b>Country ⇾</b> <code>{country_name}</code> {flag}"
    )

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Команды:\n/bin 457173\n!fake serbia")

@dp.message()
async def handler(message: types.Message):
    if not message.text:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.chat.type == "private" and user_id not in ALLOWED_USERS:
        return

    if message.chat.type in ["group", "supergroup"] and chat_id not in ALLOWED_CHATS:
        return

    text = message.text.strip().lower()

    if text.startswith("!fake"):
        args = text[5:].strip()
        if not args:
            await message.answer("❌ Example: !fake usa")
            return
        response = await fake_generator(args)
        await message.answer(response, parse_mode="HTML")
        return

    if text.startswith("/bin") or text.startswith("!bin"):
        args = text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer("❌ Пример: /bin 457173")
            return
        response = await bin_lookup(args[1])
        await message.answer(response, parse_mode="HTML")
        return

# ================== RUN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
