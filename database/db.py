"""
Подключение к SQLite и контекстный менеджер для транзакций.
"""
import sqlite3
from pathlib import Path

import config
from database.schema import init_schema


def get_connection() -> sqlite3.Connection:
    """Открывает соединение с БД и включает WAL для лучшей конкурентности."""
    db_path = Path(config.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Инициализирует схему при старте приложения."""
    conn = get_connection()
    try:
        init_schema(conn)
    finally:
        conn.close()
