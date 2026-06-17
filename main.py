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

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
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

# --- ВРЕМЯ ЭВОЛЮЦИИ (в секундах) ---
TIME_TO_HATCH = 120    # 2 минуты до вылупления яйца
TIME_TO_GROW = 600     # 10 минут от младенца до Скриптика
TIME_TO_FINAL = 1200   # 20 минут до Кибер-Кота

# --- ЛОГИКА ЖИЗНИ И ВРЕМЕНИ ---
def get_updated_pet(user_id):
    cursor.execute("SELECT name, stage, satiety, energy, last_update, born_time, is_sleeping FROM pets WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    
    name, stage, satiety, energy, last_update, born_time, is_sleeping = row
    current_time = int(time.time())
    time_passed = current_time - last_update
    total_age = current_time - born_time
    
    # 1. Изменение характеристик
    if not is_sleeping:
        decay = int((time_passed / 3600.0) * 5) # -5 в час
        if decay > 0:
            satiety = max(0, satiety - decay)
            energy = max(0, energy - decay)
    else:
        energy_gain = int((time_passed / 3600.0) * 15) # +15 в час во сне
        satiety_decay = int((time_passed / 3600.0) * 2) # -2 в час во сне
        if energy_gain > 0:
            energy = min(100, energy + energy_gain)
            satiety = max(0, satiety - satiety_decay)

    # 2. Эволюция и смерть
    if satiety <= 0 and stage != "Ошибка 404":
        stage = "Ошибка 404"
        is_sleeping = 0
    elif stage == "Яйцо" and total_age >= TIME_TO_HATCH:
        stage = "Младенец"
        satiety, energy = 60, 60
    elif stage == "Младенец" and total_age >= TIME_TO_GROW:
        stage = "Скриптик"
    elif stage == "Скриптик" and satiety > 80 and total_age >= TIME_TO_FINAL:
        stage = "Кибер-Кот"
        
    cursor.execute("""
        UPDATE pets 
        SET satiety = ?, energy = ?, stage = ?, last_update = ?, is_sleeping = ?
        WHERE user_id = ?
    """, (satiety, energy, stage, current_time, is_sleeping, user_id))
    conn.commit()
    
    return {
        "name": name, "stage": stage, "satiety": satiety, 
        "energy": energy, "is_sleeping": is_sleeping, "total_age": total_age
    }

# --- КЛАВИАТУРА ---
def get_main_keyboard(is_sleeping=False, stage=""):
    if stage == "Ошибка 404":
        return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔄 Начать заново")]], resize_keyboard=True)
    
    sleep_btn = "⏰ Проснуться" if is_sleeping else "💤 Уложить спать"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍖 Покормить"), KeyboardButton(text=sleep_btn)],
            [KeyboardButton(text="📊 Статус")]
        ],
        resize_keyboard=True
    )

# --- ОТПРАВКА КАРТИНОК С УМНОЙ ПРОВЕРКОЙ ---
async def send_smart_photo(message: Message, photo_id: str, caption: str, reply_markup=None):
    """Пытается отправить фото. Если это заглушка, отправляет текст с предупреждением."""
    if photo_id.startswith("PLACEHOLDER"):
        warning = "\n\n🖼 *(Тут должна быть картинка. Отправь мне фото, скопируй ID и вставь в config.py)*"
        await message.answer(caption + warning, reply_markup=reply_markup)
    else:
        try:
            await message.answer_photo(photo=photo_id, caption=caption, reply_markup=reply_markup)
        except Exception:
            await message.answer(caption + "\n\n❌ *(Ошибка: неверный file_id в config.py!)*", reply_markup=reply_markup)

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    pet = get_updated_pet(user_id)
    
    if not pet:
        current_time = int(time.time())
        cursor.execute("""
            INSERT INTO pets (user_id, name, stage, satiety, energy, last_update, born_time, is_sleeping)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (user_id, "Скриптик", "Яйцо", 100, 100, current_time, current_time))
        conn.commit()
        
        await send_smart_photo(
            message, config.IMAGES["egg"], 
            "🥚 Ты получил загадочное цифровое яйцо!\nОно теплое на ощупь. Следи за статусом, чтобы узнать, когда оно вылупится.",
            get_main_keyboard(stage="Яйцо")
        )
    else:
        await message.answer("Твой питомец уже здесь!", reply_markup=get_main_keyboard(pet['is_sleeping'], pet['stage']))

@dp.message(F.text == "🔄 Начать заново")
async def restart_game(message: Message):
    cursor.execute("DELETE FROM pets WHERE user_id = ?", (message.from_user.id,))
    conn.commit()
    await cmd_start(message)

@dp.message(F.text == "📊 Статус")
async def pet_status(message: Message):
    pet = get_updated_pet(message.from_user.id)
    if not pet: return await message.answer("Сначала напиши /start")
    
    # Расчет таймеров
    timer_text = ""
    if pet['stage'] == "Яйцо":
        left = max(0, TIME_TO_HATCH - pet['total_age'])
        timer_text = f"\n⏳ До вылупления: {left} сек."
    elif pet['stage'] == "Младенец":
        left = max(0, TIME_TO_GROW - pet['total_age'])
        timer_text = f"\n⏳ До взросления: {left // 60} мин {left % 60} сек."
    elif pet['stage'] == "Скриптик":
        left = max(0, TIME_TO_FINAL - pet['total_age'])
        timer_text = f"\n⏳ До финальной эволюции: {left // 60} мин {left % 60} сек."

    # Прогресс-бары
    sat_bar = "🟩" * (pet['satiety'] // 10) + "⬜" * (10 - (pet['satiety'] // 10))
    en_bar = "🟨" * (pet['energy'] // 10) + "⬜" * (10 - (pet['energy'] // 10))
    
    status_text = (
        f"👾 Имя: {pet['name']}\n"
        f"🧬 Стадия: {pet['stage']}{timer_text}\n"
        f"🍖 Сытость: {pet['satiety']}% [{sat_bar}]\n"
        f"⚡ Энергия: {pet['energy']}% [{en_bar}]\n"
        f"🛌 Состояние: {'Спит 💤' if pet['is_sleeping'] else 'Бодрствует 🐾'}"
    )
    
    # Выбор картинки
    if pet['is_sleeping']:
        photo_id = config.IMAGES["sleep"]
    else:
        stage_images = {
            "Яйцо": config.IMAGES["egg"],
            "Младенец": config.IMAGES["baby"],
            "Скриптик": config.IMAGES["grows"],
            "Кибер-Кот": config.IMAGES["cat"],
            "Ошибка 404": config.IMAGES["error404"]
        }
        photo_id = stage_images.get(pet['stage'])
    
    await send_smart_photo(message, photo_id, status_text)

@dp.message(F.text == "🍖 Покормить")
async def feed_pet(message: Message):
    pet = get_updated_pet(message.from_user.id)
    if not pet: return
    
    if pet['stage'] == "Ошибка 404":
        return await message.answer("Мертвые пиксели не едят...")
    if pet['is_sleeping']:
        return await message.answer("Тссс, он спит! Сначала разбуди его.")
    if pet['stage'] == "Яйцо":
        return await message.answer("Яйцо нельзя кормить. Подожди, пока оно вылупится (нажми 'Статус').")

    new_sat = min(100, pet['satiety'] + 20)
    cursor.execute("UPDATE pets SET satiety = ?, last_update = ? WHERE user_id = ?", (new_sat, int(time.time()), message.from_user.id))
    conn.commit()
    
    await send_smart_photo(message, config.IMAGES["feed"], "Ням-ням! Ты покормил питомца (+20 сытости).")

@dp.message(F.text.in_({"💤 Уложить спать", "⏰ Проснуться"}))
async def toggle_sleep(message: Message):
    pet = get_updated_pet(message.from_user.id)
    if not pet: return
    
    if pet['stage'] in ["Ошибка 404", "Яйцо"]:
        return await message.answer("Сейчас это действие недоступно.")
        
    new_sleep = 0 if pet['is_sleeping'] else 1
    cursor.execute("UPDATE pets SET is_sleeping = ?, last_update = ? WHERE user_id = ?", (new_sleep, int(time.time()), message.from_user.id))
    conn.commit()
    
    if new_sleep == 1:
        await send_smart_photo(message, config.IMAGES["sleep"], "Пип-пип... Система переходит в спящий режим. Энергия восстанавливается.", get_main_keyboard(True, pet['stage']))
    else:
        photo = config.IMAGES["baby"] if pet['stage'] == "Младенец" else config.IMAGES["grows"]
        if pet['stage'] == "Кибер-Кот": photo = config.IMAGES["cat"]
        await send_smart_photo(message, photo, "Бодрое утро! Питомец готов к активности.", get_main_keyboard(False, pet['stage']))

# --- ПЕРЕХВАТЧИК КАРТИНОК (Чтобы настроить config.py) ---
@dp.message(F.photo)
async def catch_file_id(message: Message):
    file_id = message.photo[-1].file_id
    await message.reply(
        f"Отлично! Вот ID этой картинки:\n\n`{file_id}`\n\n"
        f"Скопируй этот текст и вставь его в файл `config.py` в нужную строчку.", 
        parse_mode="MarkdownV2"
    )

if __name__ == "__main__":
    dp.run_polling(bot)
