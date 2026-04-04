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

ALLOWED_USERS = {8270778815, 7979473115, 1003539611, 8412856341, 7215287573}
ALLOWED_CHATS = {-1003392192892}

# ================== LOGGING ==================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================== CACHE ==================
BIN_CACHE = {}

# ================== COUNTRY → LOCALE ==================
COUNTRY_TO_LOCALE = {
    # Европа
    "germany": "de_DE", "france": "fr_FR", "spain": "es_ES",
    "italy": "it_IT", "netherlands": "nl_NL", "belgium": "nl_BE",
    "sweden": "sv_SE", "norway": "no_NO", "finland": "fi_FI",
    "denmark": "da_DK", "poland": "pl_PL", "czech": "cs_CZ",
    "slovakia": "sk_SK", "hungary": "hu_HU", "romania": "ro_RO",
    "bulgaria": "bg_BG", "greece": "el_GR", "portugal": "pt_PT",
    "ukraine": "uk_UA", "russia": "ru_RU",

    # Балканы fallback
    "serbia": "hr_HR", "bosnia": "hr_HR", "montenegro": "hr_HR",

    # Америка
    "usa": "en_US", "canada": "en_CA", "mexico": "es_MX",
    "brazil": "pt_BR", "argentina": "es_AR",

    # Азия
    "japan": "ja_JP", "korea": "ko_KR", "china": "zh_CN",
    "india": "en_IN", "thailand": "th_TH", "vietnam": "vi_VN",

    # Африка
    "nigeria": "en_NG", "kenya": "en_KE", "egypt": "ar_EG",

    # Океания
    "australia": "en_AU", "newzealand": "en_NZ",

    "default": "en_US"
}

# ================== ALIASES ==================
ALIASES = {
    "us": "usa", "ru": "russia", "ua": "ukraine",
    "de": "germany", "fr": "france", "es": "spain",
    "it": "italy", "au": "australia", "rs": "serbia"
}

# ================== FLAG ==================
def country_flag(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🏳️"
    code = country_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - ord('A')) + chr(0x1F1E6 + ord(code[1]) - ord('A'))

# ================== FAKE ==================
def resolve_country(user_input: str):
    user_input = user_input.lower()

    # alias
    user_input = ALIASES.get(user_input, user_input)

    # random
    if user_input == "random":
        return random.choice(list(COUNTRY_TO_LOCALE.keys()))

    # partial match
    matches = [c for c in COUNTRY_TO_LOCALE if user_input in c]
    if matches:
        return matches[0]

    return user_input

async def fake_generator(country_input: str) -> str:
    country = resolve_country(country_input)

    locale = COUNTRY_TO_LOCALE.get(country, COUNTRY_TO_LOCALE["default"])

    if locale not in AVAILABLE_LOCALES:
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

    email = fake.email()

    raw_phone = fake.phone_number()
    phone = ''.join(c for c in raw_phone if c.isdigit() or c == '+')

    return (
        f"<b>Name ⇾</b> <code>{name}</code>\n\n"
        f"<b>Street ⇾</b> <code>{street}</code>\n"
        f"<b>City ⇾</b> <code>{city}</code>\n"
        f"<b>State ⇾</b> <code>{state}</code>\n"
        f"<b>ZIP ⇾</b> <code>{zip_code}</code>\n\n"
        f"<b>Country ⇾</b> <code>{country.upper()}</code>\n"
        f"<b>Email ⇾</b> <code>{email}</code>\n"
        f"<b>Phone ⇾</b> <code>{phone}</code>"
    )

# ================== BIN ==================
async def fetch_bin(bin_number: str):
    url = f"https://data.handyapi.com/bin/{bin_number}"
    headers = {"x-api-key": API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            try:
                return await resp.json()
            except:
                return None

async def bin_lookup(bin_number: str) -> str:
    bin_number = ''.join(c for c in bin_number if c.isdigit())

    if len(bin_number) < 6:
        return "❌ Введи минимум 6 цифр."

    data = await fetch_bin(bin_number)

    if not data or data.get("Status") != "SUCCESS":
        return "❌ BIN не найден."

    return (
        f"<b>Scheme ⇾</b> {data.get('Scheme')}\n"
        f"<b>Type ⇾</b> {data.get('Type')}\n"
        f"<b>Bank ⇾</b> {data.get('Issuer')}"
    )

# ================== HANDLERS ==================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🔥 BIN + Fake Generator PRO\n\n"
        "Команды:\n"
        "!fake usa\n"
        "!fake ger\n"
        "!fake random\n"
        "!fake list\n"
        "/bin 457173"
    )

@dp.message()
async def handler(message: types.Message):
    text = (message.text or "").strip().lower()

    if text.startswith("!fake"):
        args = text[5:].strip()

        if args == "list":
            countries = "\n".join(sorted(COUNTRY_TO_LOCALE.keys()))
            await message.answer(f"<b>🌍 Countries:</b>\n{countries}")
            return

        if not args:
            await message.answer("❌ Example: !fake usa")
            return

        response = await fake_generator(args)
        await message.answer(response, parse_mode="HTML")
        return

    if text.startswith("/bin") or text.startswith("!bin"):
        args = text[4:].strip()

        if not args:
            await message.answer("❌ Example: /bin 457173")
            return

        response = await bin_lookup(args)
        await message.answer(response, parse_mode="HTML")

# ================== RUN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
