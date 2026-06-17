import sqlite3
import time

DB_NAME = "tamagotchi.db"

def init_db():
    """Создает таблицу, если её нет"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                pet_name TEXT DEFAULT 'Скриптик',
                satiety REAL DEFAULT 100.0,
                energy REAL DEFAULT 100.0,
                last_update INTEGER
            )
        ''')
        conn.commit()

def get_user(user_id):
    """Получает данные игрока"""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

def create_user(user_id):
    """Регистрирует нового игрока с текущим временем"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, last_update) VALUES (?, ?)",
            (user_id, int(time.time()))
        )
        conn.commit()

def update_user(user_id, satiety, energy, last_update):
    """Обновляет параметры питомца"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET satiety = ?, energy = ?, last_update = ? 
            WHERE user_id = ?
        ''', (satiety, energy, last_update, user_id))
        conn.commit()
