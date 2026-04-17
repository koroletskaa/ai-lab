"""
Модуль для роботи з базою даних SQLite
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "emotion_tracker.db"


def get_db_connection():
    """Створює підключення до бази даних"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Дозволяє звертатися до колонок по назві
    return conn


def init_db():
    """Ініціалізує базу даних (створює файл якщо не існує)"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    conn.close()

