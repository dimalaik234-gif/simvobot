import sys
import time
import sqlite3
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Инициализация БД
conn = sqlite3.connect("tamagotchi.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS pets (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    stage TEXT,
    satiety INTEGER,
    energy INTEGER,
    last_update INTEGER,
    born_time INTEGER,
    is_sleeping INTEGER DEFAULT 0
)
""")
conn.commit()

# --- ВСПОМОГАТЕЛЬНАЯ ЛОГИКА ---
def get_updated_pet(user_id):
    """Извлекает данные, считает пассивное время и эволюцию"""
    cursor.execute("SELECT name, stage, satiety, energy, last_update, born_time, is_sleeping FROM pets WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    
    name, stage, satiety, energy, last_update, born_time, is_sleeping = row
    current_time = int(time.time())
    time_passed = current_time - last_update
    total_age = current_time - born_time
    
    # 1. Пассивное падение характеристик (если питомец не спит)
    if not is_sleeping:
        # Теряет 5 единиц сытости и энергии в час
        decay = int((time_passed / 3600.0) * 5)
        if decay > 0:
            satiety = max(0, satiety - decay)
            energy = max(0, energy - decay)
    else:
        # Если спит, энергия растет (например, +15 в час), а сытость падает чуть медленнее (-2 в час)
        energy_gain = int((time_passed / 3600.0) * 15)
        satiety_decay = int((time_passed / 3600.0) * 2)
        if energy_gain > 0:
            energy = min(100, energy + energy_gain)
            satiety = max(0, satiety - satiety_decay)

    # 2. АВТОМАТИЧЕСКАЯ ЭВОЛЮЦИЯ (Временные интервалы для теста можно уменьшить)
    # Яйцо вылупляется через 2 минуты (120 секунд) после старта
    if stage == "Яйцо" and total_age >= 120:
        stage = "Младенец"
        satiety = 60
        energy = 60
    # Младенец растет в Скриптика через 10 минут (600 секунд)
    elif stage == "Младенец" and total_age >= 600:
        stage = "Скриптик"
    
    # Смерть / Ошибка 404
    if satiety <= 0 and stage != "Ошибка 404":
        stage = "Ошибка 404"
    # Финальная эволюция в Кибер-Кота (если Скриптик сыт и здоров, например через 20 минут общего времени)
    elif stage == "Скриптик" and satiety > 80 and total_age >= 1200:
        stage = "Кибер-Кот"
        
    # Сохраняем изменения
    cursor.execute("""
        UPDATE pets 
        SET satiety = ?, energy = ?, stage = ?, last_update = ?
        WHERE user_id = ?
    """, (satiety, energy, stage, current_time, user_id))
    conn.commit()
    
    return {"name": name, "stage": stage, "satiety": satiety, "energy": energy, "is_sleeping": is_sleeping}

def get_main_keyboard(is_sleeping=False):
    """Клавиатура меняется в зависимости от того, спит бот или нет"""
    sleep_btn = "⏰ Проснуться" if is_sleeping else "💤 Уложить спать"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍖 Покормить"), KeyboardButton(text=sleep_btn)],
            [KeyboardButton(text="📊 Статус")]
        ],
        resize_keyboard=True
    )

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    pet = get_updated_pet(user_id)
    
    if not pet:
        current_time = int(time.time())
        # НАЧАЛО С ЯЙЦА
        cursor.execute("""
            INSERT INTO pets (user_id, name, stage, satiety, energy, last_update, born_time, is_sleeping)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (user_id, "Скриптик", "Яйцо", 100, 100, current_time, current_time))
        conn.commit()
        
        status_text = "🥚 Ты получил загадочное цифровое яйцо! Подожди немного, пока оно начнет трескаться..."
        try:
            await message.answer_photo(photo=config.IMAGES.get("egg"), caption=status_text, reply_markup=get_main_keyboard())
        except Exception:
            await message.answer(status_text, reply_markup=get_main_keyboard())
    else:
        await message.answer("Скриптик уже ждет тебя!", reply_markup=get_main_keyboard(pet['is_sleeping']))

@dp.message(F.text == "📊 Статус")
async def pet_status(message: Message):
    pet = get_updated_pet(message.from_user.id)
    if not pet: return
    
    sat_bar = "🟩" * (pet['satiety'] // 10) + "⬜" * (10 - (pet['satiety'] // 10))
    en_bar = "🟨" * (pet['energy'] // 10) + "⬜" * (10 - (pet['energy'] // 10))
    
    status_text = (
        f"👾 Имя: {pet['name']}\n"
        f"🧬 Стадия: {pet['stage']}\n"
        f"🍖 Сытость: {pet['satiety']}% [{sat_bar}]\n"
        f"⚡ Энергия: {pet['energy']}% [{en_bar}]\n"
        f" Состояние: {'Спит 💤' if pet['is_sleeping'] else 'Бодрствует 🐾'}"
    )
    
    # Динамический выбор картинки для СТАТУСА
    if pet['is_sleeping']:
        photo_id = config.IMAGES.get("sleep")  # Если спит — всегда картинка сна
    else:
        # Иначе картинка строго по его возрасту/стадии
        stage_images = {
            "Яйцо": config.IMAGES.get("egg"),
            "Младенец": config.IMAGES.get("baby"),
            "Скриптик": config.IMAGES.get("grows"),
            "Кибер-Кот": config.IMAGES.get("cat"),
            "Ошибка 404": config.IMAGES.get("error404")
        }
        photo_id = stage_images.get(pet['stage'])
    
    try:
        await message.answer_photo(photo=photo_id, caption=status_text)
    except Exception:
        await message.answer(status_text + "\n\n*(Графика настраивается)*")

@dp.message(F.text == "🍖 Покормить")
async def feed_pet(message: Message):
    user_id = message.from_user.id
    pet = get_updated_pet(user_id)
    if not pet: return
    
    if pet['stage'] == "Ошибка 404":
        return await message.answer("Ему уже ничего не поможет...")
    if pet['is_sleeping']:
        return await message.answer("Тссс, Скриптик спит! Не надо его кормить.")
    if pet['stage'] == "Яйцо":
        return await message.answer("Яйцо нельзя покормить, нужно дождаться вылупления!")

    new_satiety = min(100, pet['satiety'] + 20)
    cursor.execute("UPDATE pets SET satiety = ?, last_update = ? WHERE user_id = ?", (new_satiety, int(time.time()), user_id))
    conn.commit()
    
    # КОРМЛЕНИЕ: Показываем картинку кормления ("feed"), только если это не заглушка
    try:
        await message.answer_photo(photo=config.IMAGES.get("feed"), caption="Ням-ням! Питомец доволен!")
    except Exception:
        await message.answer("Ням-ням! Питомец доволен!")

@dp.message(F.text.in_({"💤 Уложить спать", "⏰ Проснуться"}))
async def toggle_sleep(message: Message):
    user_id = message.from_user.id
    pet = get_updated_pet(user_id)
    if not pet: return
    
    if pet['stage'] == "Яйцо":
        return await message.answer("Яйцо не может спать по команде.")
        
    # Переключаем статус сна
    new_sleep_state = 0 if pet['is_sleeping'] else 1
    cursor.execute("UPDATE pets SET is_sleeping = ?, last_update = ? WHERE user_id = ?", (new_sleep_state, int(time.time()), user_id))
    conn.commit()
    
    if new_sleep_state == 1:
        text = "Хр-р-р... Скриптик уснул. Энергия восстанавливается."
        photo = config.IMAGES.get("sleep")
    else:
        text = "Скриптик проснулся и готов к приключениям!"
        photo = config.IMAGES.get("baby" if pet['stage'] == "Младенец" else "grows")

    try:
        await message.answer_photo(photo=photo, caption=text, reply_markup=get_main_keyboard(new_sleep_state))
    except Exception:
        await message.answer(text, reply_markup=get_main_keyboard(new_sleep_state))

# Перехватчик file_id
@dp.message(F.photo)
async def catch_file_id(message: Message):
    file_id = message.photo[-1].file_id
    await message.reply(f"Перехват file_id картинки:\n\n`{file_id}`", parse_mode="MarkdownV2")

if __name__ == "__main__":
    dp.run_polling(bot)

