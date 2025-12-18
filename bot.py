import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключение к БД
def init_db():
    conn = sqlite3.connect("referral.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referrer_id INTEGER,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    "")
    conn.commit()
    conn.close()

def add_user(user_id: int, referrer_id: int = None):
    conn = sqlite3.connect("referral.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, referrer_id) VALUES (?, ?)",
        (user_id, referrer_id)
    )
    conn.commit()
    conn.close()

def get_referral_count(user_id: int) -> int:
    conn = sqlite3.connect("referral.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE referrer_id = ?",
        (user_id,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_referrer(user_id: int) -> int | None:
    conn = sqlite3.connect("referral.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT referrer_id FROM users WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Команда /start с реферальным параметром
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()

    # Извлекаем реферальный ID, если есть
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            # Не засчитываем самоприглашения
            if referrer_id == user_id:
                referrer_id = None
        except ValueError:
            pass

    # Регистрируем пользователя
    add_user(user_id, referrer_id)

    # Формируем реферальную ссылку
    ref_link = f"https://t.me/your_bot_username?start={user_id}"

    # Клавиатура с кнопкой реферальной ссылки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Поделиться ссылкой", url=ref_link)]
    ])

    count = get_referral_count(user_id)

    await message.answer(
        f!Привет!\n\n"
        f"Ваша реферальная ссылка:\n{ref_link}\n\n"
        f"Вы пригласили: {count} пользователей.",
        reply_markup=keyboard
    )

# Команда /stats — статистика
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    count = get_referral_count(user_id)
    await message.answer(f"Вы пригласили: {count} пользователей.")

# Запуск бота
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
