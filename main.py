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

# Сюда нужно вставить file_id картинок, которые мы сгенерировали
# Полный архив картинок для всех стадий жизни Скриптика
IMAGES = {
    "egg": "{
 "update_id": 938106071,
 "message": {
  "message_id": 2806148,
  "from": {
   "id": 7184353531,
   "is_bot": false,
   "first_name": "^._.^",
   "username": "dreinw0",
   "language_code": "ru"
  },
  "chat": {
   "id": 7184353531,
   "first_name": "^._.^",
   "username": "dreinw0",
   "type": "private"
  },
  "date": 1781697656,
  "photo": [
   {
    "file_id": "AgACAgIAAxkBAAEq0YRqMox4K8zQfyQifqRqoMKGgev3ZwACqxxrGxvakUmI9XL5NsIH6QEAAwIAA3MAAzwE",
    "file_unique_id": "AQADqxxrGxvakUl4",
    "file_size": 687,
    "width": 90,
    "height": 49
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0YRqMox4K8zQfyQifqRqoMKGgev3ZwACqxxrGxvakUmI9XL5NsIH6QEAAwIAA20AAzwE",
    "file_unique_id": "AQADqxxrGxvakUly",
    "file_size": 7105,
    "width": 320,
    "height": 174
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0YRqMox4K8zQfyQifqRqoMKGgev3ZwACqxxrGxvakUmI9XL5NsIH6QEAAwIAA3gAAzwE",
    "file_unique_id": "AQADqxxrGxvakUl9",
    "file_size": 35753,
    "width": 800,
    "height": 436
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0YRqMox4K8zQfyQifqRqoMKGgev3ZwACqxxrGxvakUmI9XL5NsIH6QEAAwIAA3kAAzwE",
    "file_unique_id": "AQADqxxrGxvakUl-",
    "file_size": 82032,
    "width": 1280,
    "height": 698
   }
  ]
 }
}",        # Яйцо на деревянной подставке
    "baby": "{
 "update_id": 938106092,
 "message": {
  "message_id": 2806179,
  "from": {
   "id": 7184353531,
   "is_bot": false,
   "first_name": "^._.^",
   "username": "dreinw0",
   "language_code": "ru"
  },
  "chat": {
   "id": 7184353531,
   "first_name": "^._.^",
   "username": "dreinw0",
   "type": "private"
  },
  "date": 1781697827,
  "photo": [
   {
    "file_id": "AgACAgIAAxkBAAEq0aNqMo0jsheksMYEJQ39I6zFTZwtsgACrhxrGxvakUn43UGRjwQftQEAAwIAA3MAAzwE",
    "file_unique_id": "AQADrhxrGxvakUl4",
    "file_size": 708,
    "width": 90,
    "height": 49
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0aNqMo0jsheksMYEJQ39I6zFTZwtsgACrhxrGxvakUn43UGRjwQftQEAAwIAA20AAzwE",
    "file_unique_id": "AQADrhxrGxvakUly",
    "file_size": 8132,
    "width": 320,
    "height": 174
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0aNqMo0jsheksMYEJQ39I6zFTZwtsgACrhxrGxvakUn43UGRjwQftQEAAwIAA3gAAzwE",
    "file_unique_id": "AQADrhxrGxvakUl9",
    "file_size": 41989,
    "width": 800,
    "height": 436
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0aNqMo0jsheksMYEJQ39I6zFTZwtsgACrhxrGxvakUn43UGRjwQftQEAAwIAA3kAAzwE",
    "file_unique_id": "AQADrhxrGxvakUl-",
    "file_size": 91096,
    "width": 1280,
    "height": 698
   }
  ]
 }
}",       # Вылупившийся зеленый слизень (основной экран)
    "teen_good": "{
 "update_id": 938106094,
 "message": {
  "message_id": 2806181,
  "from": {
   "id": 7184353531,
   "is_bot": false,
   "first_name": "^._.^",
   "username": "dreinw0",
   "language_code": "ru"
  },
  "chat": {
   "id": 7184353531,
   "first_name": "^._.^",
   "username": "dreinw0",
   "type": "private"
  },
  "date": 1781697840,
  "photo": [
   {
    "file_id": "AgACAgIAAxkBAAEq0aVqMo0wnFxwwfdmaMWw7Zm_Gx59hAACrxxrGxvakUlzeA_YOnbpagEAAwIAA3MAAzwE",
    "file_unique_id": "AQADrxxrGxvakUl4",
    "file_size": 731,
    "width": 90,
    "height": 49
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0aVqMo0wnFxwwfdmaMWw7Zm_Gx59hAACrxxrGxvakUlzeA_YOnbpagEAAwIAA20AAzwE",
    "file_unique_id": "AQADrxxrGxvakUly",
    "file_size": 9077,
    "width": 320,
    "height": 174
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0aVqMo0wnFxwwfdmaMWw7Zm_Gx59hAACrxxrGxvakUlzeA_YOnbpagEAAwIAA3gAAzwE",
    "file_unique_id": "AQADrxxrGxvakUl9",
    "file_size": 47180,
    "width": 800,
    "height": 436
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0aVqMo0wnFxwwfdmaMWw7Zm_Gx59hAACrxxrGxvakUlzeA_YOnbpagEAAwIAA3kAAzwE",
    "file_unique_id": "AQADrxxrGxvakUl-",
    "file_size": 99826,
    "width": 1280,
    "height": 698
   }
  ]
 }
}",  # Подросток с лапками (хороший уход)
    "teen_bad": "{
 "update_id": 938106096,
 "message": {
  "message_id": 2806183,
  "from": {
   "id": 7184353531,
   "is_bot": false,
   "first_name": "^._.^",
   "username": "dreinw0",
   "language_code": "ru"
  },
  "chat": {
   "id": 7184353531,
   "first_name": "^._.^",
   "username": "dreinw0",
   "type": "private"
  },
  "date": 1781697850,
  "photo": [
   {
    "file_id": "AgACAgIAAxkBAAEq0adqMo06YXC6ToSyKu2k_9cDCAwzggACsBxrGxvakUmhQNPK3VYIHAEAAwIAA3MAAzwE",
    "file_unique_id": "AQADsBxrGxvakUl4",
    "file_size": 773,
    "width": 90,
    "height": 49
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0adqMo06YXC6ToSyKu2k_9cDCAwzggACsBxrGxvakUmhQNPK3VYIHAEAAwIAA20AAzwE",
    "file_unique_id": "AQADsBxrGxvakUly",
    "file_size": 9236,
    "width": 320,
    "height": 174
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0adqMo06YXC6ToSyKu2k_9cDCAwzggACsBxrGxvakUmhQNPK3VYIHAEAAwIAA3gAAzwE",
    "file_unique_id": "AQADsBxrGxvakUl9",
    "file_size": 47457,
    "width": 800,
    "height": 436
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0adqMo06YXC6ToSyKu2k_9cDCAwzggACsBxrGxvakUmhQNPK3VYIHAEAAwIAA3kAAzwE",
    "file_unique_id": "AQADsBxrGxvakUl-",
    "file_size": 100379,
    "width": 1280,
    "height": 698
   }
  ]
 }
}",   # Подросток грустный/темный (плохой уход)
    "adult_good": "{
 "update_id": 938106097,
 "message": {
  "message_id": 2806185,
  "from": {
   "id": 7184353531,
   "is_bot": false,
   "first_name": "^._.^",
   "username": "dreinw0",
   "language_code": "ru"
  },
  "chat": {
   "id": 7184353531,
   "first_name": "^._.^",
   "username": "dreinw0",
   "type": "private"
  },
  "date": 1781697860,
  "photo": [
   {
    "file_id": "AgACAgIAAxkBAAEq0alqMo1EhfWa-4nz6J3QxJC0K1gK3wACsRxrGxvakUnoVJYEIjNrKQEAAwIAA3MAAzwE",
    "file_unique_id": "AQADsRxrGxvakUl4",
    "file_size": 817,
    "width": 90,
    "height": 49
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0alqMo1EhfWa-4nz6J3QxJC0K1gK3wACsRxrGxvakUnoVJYEIjNrKQEAAwIAA20AAzwE",
    "file_unique_id": "AQADsRxrGxvakUly",
    "file_size": 11534,
    "width": 320,
    "height": 174
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0alqMo1EhfWa-4nz6J3QxJC0K1gK3wACsRxrGxvakUnoVJYEIjNrKQEAAwIAA3gAAzwE",
    "file_unique_id": "AQADsRxrGxvakUl9",
    "file_size": 60643,
    "width": 800,
    "height": 436
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0alqMo1EhfWa-4nz6J3QxJC0K1gK3wACsRxrGxvakUnoVJYEIjNrKQEAAwIAA3kAAzwE",
    "file_unique_id": "AQADsRxrGxvakUl-",
    "file_size": 124741,
    "width": 1280,
    "height": 698
   }
  ]
 }
}", # Финальная форма: Кибер-Кот
    "adult_bad": "{
 "update_id": 938106098,
 "message": {
  "message_id": 2806187,
  "from": {
   "id": 7184353531,
   "is_bot": false,
   "first_name": "^._.^",
   "username": "dreinw0",
   "language_code": "ru"
  },
  "chat": {
   "id": 7184353531,
   "first_name": "^._.^",
   "username": "dreinw0",
   "type": "private"
  },
  "date": 1781697870,
  "photo": [
   {
    "file_id": "AgACAgIAAxkBAAEq0atqMo1OKTzPwFA4d-d3lhljC5er5gACsxxrGxvakUniFL8DdWq9QAEAAwIAA3MAAzwE",
    "file_unique_id": "AQADsxxrGxvakUl4",
    "file_size": 845,
    "width": 90,
    "height": 49
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0atqMo1OKTzPwFA4d-d3lhljC5er5gACsxxrGxvakUniFL8DdWq9QAEAAwIAA20AAzwE",
    "file_unique_id": "AQADsxxrGxvakUly",
    "file_size": 12231,
    "width": 320,
    "height": 174
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0atqMo1OKTzPwFA4d-d3lhljC5er5gACsxxrGxvakUniFL8DdWq9QAEAAwIAA3gAAzwE",
    "file_unique_id": "AQADsxxrGxvakUl9",
    "file_size": 64172,
    "width": 800,
    "height": 436
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0atqMo1OKTzPwFA4d-d3lhljC5er5gACsxxrGxvakUniFL8DdWq9QAEAAwIAA3kAAzwE",
    "file_unique_id": "AQADsxxrGxvakUl-",
    "file_size": 130275,
    "width": 1280,
    "height": 698
   }
  ]
 }
}",  # Финальная форма: Ошибка 404 / Смерть
    "sleep": "{
 "update_id": 938106099,
 "message": {
  "message_id": 2806189,
  "from": {
   "id": 7184353531,
   "is_bot": false,
   "first_name": "^._.^",
   "username": "dreinw0",
   "language_code": "ru"
  },
  "chat": {
   "id": 7184353531,
   "first_name": "^._.^",
   "username": "dreinw0",
   "type": "private"
  },
  "date": 1781697881,
  "photo": [
   {
    "file_id": "AgACAgIAAxkBAAEq0a1qMo1ZsbBGxylZ6IznSlpihaYENwACtBxrGxvakUlyUh4ldTkyFgEAAwIAA3MAAzwE",
    "file_unique_id": "AQADtBxrGxvakUl4",
    "file_size": 757,
    "width": 90,
    "height": 49
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0a1qMo1ZsbBGxylZ6IznSlpihaYENwACtBxrGxvakUlyUh4ldTkyFgEAAwIAA20AAzwE",
    "file_unique_id": "AQADtBxrGxvakUly",
    "file_size": 10783,
    "width": 320,
    "height": 174
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0a1qMo1ZsbBGxylZ6IznSlpihaYENwACtBxrGxvakUlyUh4ldTkyFgEAAwIAA3gAAzwE",
    "file_unique_id": "AQADtBxrGxvakUl9",
    "file_size": 57946,
    "width": 800,
    "height": 436
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0a1qMo1ZsbBGxylZ6IznSlpihaYENwACtBxrGxvakUlyUh4ldTkyFgEAAwIAA3kAAzwE",
    "file_unique_id": "AQADtBxrGxvakUl-",
    "file_size": 119369,
    "width": 1280,
    "height": 698
   }
  ]
 }
}",      # Кибер-Кот спит калачиком
    "feed": "{
 "update_id": 938106101,
 "message": {
  "message_id": 2806193,
  "from": {
   "id": 7184353531,
   "is_bot": false,
   "first_name": "^._.^",
   "username": "dreinw0",
   "language_code": "ru"
  },
  "chat": {
   "id": 7184353531,
   "first_name": "^._.^",
   "username": "dreinw0",
   "type": "private"
  },
  "date": 1781697891,
  "photo": [
   {
    "file_id": "AgACAgIAAxkBAAEq0bFqMo1jJmt3Woadi3hX4h3RKzeyegACthxrGxvakUlmyXEsaNolxgEAAwIAA3MAAzwE",
    "file_unique_id": "AQADthxrGxvakUl4",
    "file_size": 824,
    "width": 90,
    "height": 49
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0bFqMo1jJmt3Woadi3hX4h3RKzeyegACthxrGxvakUlmyXEsaNolxgEAAwIAA20AAzwE",
    "file_unique_id": "AQADthxrGxvakUly",
    "file_size": 11535,
    "width": 320,
    "height": 174
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0bFqMo1jJmt3Woadi3hX4h3RKzeyegACthxrGxvakUlmyXEsaNolxgEAAwIAA3gAAzwE",
    "file_unique_id": "AQADthxrGxvakUl9",
    "file_size": 60791,
    "width": 800,
    "height": 436
   },
   {
    "file_id": "AgACAgIAAxkBAAEq0bFqMo1jJmt3Woadi3hX4h3RKzeyegACthxrGxvakUlmyXEsaNolxgEAAwIAA3kAAzwE",
    "file_unique_id": "AQADthxrGxvakUl-",
    "file_size": 124455,
    "width": 1280,
    "height": 698
   }
  ]
 }
}",       # Кибер-Кот ест цифровой корм
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
            # Если это клик по кнопке — плавно меняем текст меню
            await message_context.message.edit_text(text, reply_markup=make_keyboard())
        else:
            # Если это новая отправка — шлем картинку с текстом
            await bot.send_photo(chat_id=user_id, photo=photo_id, caption=text, reply_markup=make_keyboard())
    except Exception as e:
        # Костыль на случай, если file_id неверные — шлем просто текст, чтобы бот не падал
        if edit and isinstance(message_context, CallbackQuery):
            await message_context.message.edit_text(text + "\n(Ошибка загрузки фото)", reply_markup=make_keyboard())
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
    print("Бот успешно запущен локально!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
