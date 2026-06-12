"""
Лимит создания ссылок: 10 штук в день с одного IP.
"""
from __future__ import annotations
from datetime import datetime, timezone

import config
from database.db import get_connection


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def check_rate_limit(ip_address: str) -> tuple[bool, int]:
    """
    Проверяет лимит. Возвращает (можно_создать, оставшееся_количество).
    """
    day = _today_utc()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT count FROM rate_limits WHERE ip_address = ? AND day = ?",
            (ip_address, day),
        ).fetchone()
        current = row["count"] if row else 0
        remaining = max(0, config.RATE_LIMIT_PER_DAY - current)
        return current < config.RATE_LIMIT_PER_DAY, remaining
    finally:
        conn.close()


def increment_rate_limit(ip_address: str) -> None:
    """Увеличивает счётчик после успешного создания ссылки."""
    day = _today_utc()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO rate_limits (ip_address, day, count)
            VALUES (?, ?, 1)
            ON CONFLICT(ip_address, day) DO UPDATE SET count = count + 1
            """,
            (ip_address, day),
        )
        conn.commit()
    finally:
        conn.close()
