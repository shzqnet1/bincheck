import requests
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = "8612028807:AAFAh2gMp_0lrQimmGTDkeTIXgX1GlM15tA"

bot = Bot(token=TOKEN)
dp = Dispatcher()

def bin_lookup(bin_number):
    url = f"https://lookup.binlist.net/{bin_number}"
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return "❌ BIN не найден"

        data = r.json()

        return (
            f"💳 BIN: {bin_number[:6]}\n"
            f"🏦 Банк: {data.get('bank', {}).get('name', 'N/A')}\n"
            f"🌍 Страна: {data.get('country', {}).get('name', 'N/A')}\n"
            f"💼 Тип: {data.get('type', 'N/A')}\n"
            f"💳 Система: {data.get('scheme', 'N/A')}\n"
            f"🏷 Бренд: {data.get('brand', 'N/A')}"
        )

    except Exception:
        return "⚠️ Ошибка запроса к API"

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("👋 Привет! Отправь BIN (первые 6 цифр карты)")

@dp.message()
async def handle(message: Message):
    text = message.text.strip()

    if not text.isdigit() or len(text) < 6:
        await message.answer("❌ Введи минимум 6 цифр")
        return

    result = bin_lookup(text)
    await message.answer(result)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
