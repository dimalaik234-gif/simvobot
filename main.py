import sys
import time
import sqlite3
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# Импортируем настройки
import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Инициализация БД (SQLite)
conn = sqlite3.connect("tamagotchi.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS pets (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    stage TEXT,
    satiety INTEGER,
    energy INTEGER,
    last_update INTEGER
)
""")
conn.commit()

# --- ВСПОМОГАТЕЛЬНАЯ ЛОГИКА (Пассивный просчет) ---
def get_updated_pet(user_id):
    """Извлекает данные и пересчитывает показатели по разнице во времени"""
    cursor.execute("SELECT name, stage, satiety, energy, last_update FROM pets WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    
    name, stage, satiety, energy, last_update = row
    current_time = int(time.time())
    time_passed = current_time - last_update
    
    # Например, питомец теряет 5 единиц сытости и энергии в час (3600 секунд)
    hours_passed = time_passed / 3600.0
    decay = int(hours_passed * 5)
    
    if decay > 0:
        satiety = max(0, satiety - decay)
        energy = max(0, energy - decay)
        
        # Логика деградации в Ошибку 404
        if satiety <= 0 and stage != "Ошибка 404":
            stage = "Ошибка 404"
            
        # Логика эволюции в Кибер-Кота (если сытость отличная и он долго живет)
        elif satiety > 80 and stage == "Скриптик":
            stage = "Кибер-Кот"
            
        cursor.execute("""
            UPDATE pets 
            SET satiety = ?, energy = ?, stage = ?, last_update = ? 
            WHERE user_id = ?
        """, (satiety, energy, stage, current_time, user_id))
        conn.commit()
        
    return {"name": name, "stage": stage, "satiety": satiety, "energy": energy}

def get_main_keyboard():
    """Главная клавиатура (без дублирования кнопок)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍖 Покормить"), KeyboardButton(text="💤 Уложить спать")],
            [KeyboardButton(text="📊 Статус")]
        ],
        resize_keyboard=True
    )

# --- ХЕНДЛЕРЫ КОМАНД ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    pet = get_updated_pet(user_id)
    
    if not pet:
        # Регистрация нового питомца (Скриптик)
        current_time = int(time.time())
        cursor.execute("""
            INSERT INTO pets (user_id, name, stage, satiety, energy, last_update)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, "Скриптик", "Младенец", 50, 50, current_time))
        conn.commit()
        await message.answer(
            "Привет! Ты завел цифрового слизня по имени Скриптик. Заботься о нем!", 
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer("Скриптик уже ждет тебя!", reply_markup=get_main_keyboard())

@dp.message(F.text == "📊 Статус")
async def pet_status(message: Message):
    pet = get_updated_pet(message.from_user.id)
    if not pet:
        return await message.answer("Используй /start, чтобы завести питомца.")
    
    # Генерация прогресс-баров
    sat_bar = "🟩" * (pet['satiety'] // 10) + "⬜" * (10 - (pet['satiety'] // 10))
    en_bar = "🟨" * (pet['energy'] // 10) + "⬜" * (10 - (pet['energy'] // 10))
    
    status_text = (
        f"👾 Имя: {pet['name']}\n"
        f"🧬 Стадия: {pet['stage']}\n"
        f"🍖 Сытость: {pet['satiety']}% [{sat_bar}]\n"
        f"⚡ Энергия: {pet['energy']}% [{en_bar}]"
    )
    
    # Попытка отправить картинку в зависимости от стадии
    stage_images = {
        "Младенец": config.IMAGES.get("baby"),
        "Скриптик": config.IMAGES.get("grows"),
        "Кибер-Кот": config.IMAGES.get("cat"),
        "Ошибка 404": config.IMAGES.get("error404")
    }
    
    photo_id = stage_images.get(pet['stage'])
    
    try:
        # Если это заглушка, оно упадет в except и отправит только текст
        await message.answer_photo(photo=photo_id, caption=status_text)
    except Exception:
        # Защитный блок: если file_id неверный — выводим только текст
        await message.answer(status_text + "\n\n*(Графика настраивается разработчиком)*")

@dp.message(F.text == "🍖 Покормить")
async def feed_pet(message: Message):
    user_id = message.from_user.id
    pet = get_updated_pet(user_id)
    if not pet: return
    
    if pet['stage'] == "Ошибка 404":
        return await message.answer("Скриптик превратился в Ошибку 404. Похоже, ему уже ничем не помочь...")

    new_satiety = min(100, pet['satiety'] + 20)
    cursor.execute("UPDATE pets SET satiety = ?, last_update = ? WHERE user_id = ?", (new_satiety, int(time.time()), user_id))
    conn.commit()
    
    try:
        await message.answer_photo(photo=config.IMAGES.get("feed"), caption="Ням-ням! Сытость повышена.")
    except Exception:
        await message.answer("Ням-ням! Сытость повышена.")

@dp.message(F.text == "💤 Уложить спать")
async def sleep_pet(message: Message):
    user_id = message.from_user.id
    pet = get_updated_pet(user_id)
    if not pet: return
    
    if pet['stage'] == "Ошибка 404":
        return await message.answer("Система отключена. Это вечный сон...")

    new_energy = min(100, pet['energy'] + 30)
    cursor.execute("UPDATE pets SET energy = ?, last_update = ? WHERE user_id = ?", (new_energy, int(time.time()), user_id))
    conn.commit()
    
    try:
        await message.answer_photo(photo=config.IMAGES.get("sleep"), caption="Хр-р-р... Скриптик отдыхает.")
    except Exception:
        await message.answer("Хр-р-р... Скриптик отдыхает.")

# --- ФУНКЦИЯ-ПЕРЕХВАТЧИК FILE_ID ---
@dp.message(F.photo)
async def catch_file_id(message: Message):
    # Бот вернет file_id самой большой версии отправленной картинки
    file_id = message.photo[-1].file_id
    await message.reply(f"Перехват file_id картинки:\n\n`{file_id}`", parse_mode="MarkdownV2")

# --- ЗАПУСК БОТА ---
if __name__ == "__main__":
    dp.run_polling(bot)
