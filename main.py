import asyncio
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

import database as db

BOT_TOKEN = "8816734888:AAG6gApnQMqt01gfkzM-O1-L43cFnBytdgk"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# КУЛДАУНЫ И СКОРОСТЬ ПАДЕНИЯ ХАРАКТЕРИСТИК (на 1 единицу в минуту)
SATIETY_DECAY_PER_MIN = 0.5  # Голодает за ~3.3 часа
ENERGY_DECAY_PER_MIN = 0.3   # Устает за ~5.5 часов

# Чистый словарь с правильными file_id максимального качества
IMAGES = {
    "egg": "AgACAgIAAxkBAAEq0YRqMox4K8zQfyQifqRqoMKGgev3ZwACqxxrGxvakUmI9XL5NsIH6QEAAwIAA3kAAzwE",        # Яйцо на подставке
    "baby": "AgACAgIAAxkBAAEq0aNqMo0jsheksMYEJQ39I6zFTZwtsgACrhxrGxvakUn43UGRjwQftQEAAwIAA3kAAzwE",       # Зеленый слизень
    "teen_good": "AgACAgIAAxkBAAEq0aVqMo0wnFxwwfdmaMWw7Zm_Gx59hAACrxxrGxvakUlzeA_YOnbpagEAAwIAA3kAAzwE",  # Подросток (хороший уход)
    "teen_bad": "AgACAgIAAxkBAAEq0adqMo06YXC6ToSyKu2k_9cDCAwzggACsBxrGxvakUmhQNPK3VYIHAEAAwIAA3kAAzwE",   # Подросток (плохой уход)
    "adult_good": "AgACAgIAAxkBAAEq0alqMo1EhfWa-4nz6J3QxJC0K1gK3wACsRxrGxvakUnoVJYEIjNrKQEAAwIAA3kAAzwE", # Кибер-Кот
    "adult_bad": "AgACAgIAAxkBAAEq0atqMo1OKTzPwFA4d-d3lhljC5er5gACsxxrGxvakUniFL8DdWq9QAEAAwIAA3kAAzwE",  # Ошибка 404 / Смерть
    "sleep": "AgACAgIAAxkBAAEq0a1qMo1ZsbBGxylZ6IznSlpihaYENwACtBxrGxvakUlyUh4ldTkyFgEAAwIAA3kAAzwE",      # Спит калачиком
    "feed": "AgACAgIAAxkBAAEq0bFqMo1jJmt3Woadi3hX4h3RKzeyegACthxrGxvakUlmyXEsaNolxgEAAwIAA3kAAzwE",       # Ест корм
}

def calculate_passives(user_row):
    """Главная магия: считает, сколько убавилось за время отсутствия игрока"""
    current_time = int(time.time())
    time_passed_mins = (current_time - user_row['last_update']) / 60

    # Высчитываем новый голод и энергию
    new_satiety = max(0.0, user_row['satiety'] - (time_passed_mins * SATIETY_DECAY_PER_MIN))
    new_energy = max(0.0, user_row['energy'] - (time_passed_mins * ENERGY_DECAY_PER_MIN))
    
    return round(new_satiety, 1), round(new_energy, 1), current_time

def make_bar(value):
    """Рисует красивый текстовый прогресс-бар"""
    filled = int(value // 10)
    return "█" * filled + "░" * (10 - filled)

def make_keyboard():
    """Клавиатура управления питомцем"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🥩 Покормить (+20)", callback_data="action_feed"),
            InlineKeyboardButton(text="😴 Уложить спать (+40)", callback_data="action_sleep")
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить статус", callback_data="action_refresh")
        ]
    ])
@dp.message(F.photo)
async def get_photo_id(message: Message):
    print(f"ID картинки: {message.photo[-1].file_id}")
    await message.answer("ID получен, проверь логи!")


@dp.message(CommandStart())
async def start_cmd(message: Message):
    db.create_user(message.from_user.id)
    await message.answer(
        "Привет! Ты активировал код Скриптика. Заботься о нем, чтобы он вырос в Кибер-Кота!",
        reply_markup=make_keyboard()
    )
    # Сразу отправляем статус
    await send_pet_status(message.from_user.id, message)

async def send_pet_status(user_id, message_context, image_key="baby", edit=False):
    """Формирует интерфейс Тамагочи и обновляет сообщение"""
    user_row = db.get_user(user_id)
    if not user_row:
        return

    # Считаем пассивное падение шкал
    satiety, energy, current_time = calculate_passives(user_row)
    db.update_user(user_id, satiety, energy, current_time)

    # Выбираем текстовую рожицу (Каомодзи) в зависимости от состояния
    status_emoji = "( ◕‿◕ )"
    if satiety < 30 or energy < 30:
        status_emoji = "( ⋟﹏⋗ )"
    if satiety == 0 and energy == 0:
        status_emoji = "(✖╭╮✖)"

    text = (
        f"👾 **Имя:** {user_row['pet_name']}\n"
        f"Статус: {status_emoji}\n\n"
        f"🥩 **Сытость:** [{make_bar(satiety)}] {satiety}%\n"
        f"🔋 **Энергия:** [{make_bar(energy)}] {energy}%\n"
    )

    photo_id = IMAGES.get(image_key, IMAGES["baby"])

    try:
        if edit and isinstance(message_context, CallbackQuery):
            # Изменение медиа-содержимого сообщения (картинки и текста одновременно)
            from aiogram.types import InputMediaPhoto
            await message_context.message.edit_media(
                media=InputMediaPhoto(media=photo_id, caption=text),
                reply_markup=make_keyboard()
            )
        else:
            # Если это новая отправка — шлем картинку с текстом
            await bot.send_photo(chat_id=user_id, photo=photo_id, caption=text, reply_markup=make_keyboard())
    except Exception as e:
        # Резервный вариант, если что-то пойдет не так — просто обновляем текст
        if edit and isinstance(message_context, CallbackQuery):
            await message_context.message.edit_text(text + f"\n(Ошибка медиа: {e})", reply_markup=make_keyboard())
        else:
            await bot.send_message(chat_id=user_id, text=text, reply_markup=make_keyboard())

@dp.callback_query(F.data.startswith("action_"))
async def handle_actions(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_row = db.get_user(user_id)
    
    if not user_row:
        await callback.answer("Сначала напиши /start")
        return

    satiety, energy, current_time = calculate_passives(user_row)
    action = callback.data.split("_")[1]

    if action == "feed":
        if satiety >= 100:
            await callback.answer("Скриптик уже сыт под завязку! 🥩")
            return
        satiety = min(100.0, satiety + 20.0)
        db.update_user(user_id, satiety, energy, current_time)
        await callback.answer("Ням-ням! Код успешно переварен.")
        await send_pet_status(user_id, callback, image_key="feed", edit=True)

    elif action == "sleep":
        if energy >= 100:
            await callback.answer("Скриптик полон энергии и не хочет спать! ⚡")
            return
        energy = min(100.0, energy + 40.0)
        db.update_user(user_id, satiety, energy, current_time)
        await callback.answer("Скриптик ушел в режим сна... Zzz")
        await send_pet_status(user_id, callback, image_key="sleep", edit=True)

    elif action == "refresh":
        db.update_user(user_id, satiety, energy, current_time)
        await callback.answer("Статус обновлен!")
        await send_pet_status(user_id, callback, image_key="baby", edit=True)

async def main():
    db.init_db()
    # Удаляем вебхуки перед запуском, чтобы не было конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
