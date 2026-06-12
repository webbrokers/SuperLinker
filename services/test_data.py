"""
Генерация и очистка тестовых данных статистики за 30 дней.
"""
from __future__ import annotations
import random
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config
from database.db import get_connection
from services.stats import record_click


def _backup_db() -> str | None:
    """Копирует БД в data/backups/ перед деструктивной операцией."""
    src = Path(config.DATABASE_PATH)
    if not src.exists():
        return None
    backup_dir = src.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dst = backup_dir / f"superlinker_{stamp}.db"
    shutil.copy2(src, dst)
    return str(dst)


def generate_test_data(days: int = 30) -> dict:
    """
    Создаёт тестовые клики за последние N дней для существующих ссылок.
    Если ссылок нет — создаёт одну тестовую запись в links.
    """
    conn = get_connection()
    try:
        links = conn.execute("SELECT id, slug FROM links").fetchall()
        if not links:
            from services.links import create_link
            create_link("https://example.com/test-landing", title="Тестовая ссылка")
            links = conn.execute("SELECT id, slug FROM links").fetchall()

        test_ips = [
            "203.0.113.10", "198.51.100.42", "192.0.2.15",
            "10.0.0.5", "172.16.0.88",
        ]
        test_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X) Safari/17.0",
            "Mozilla/5.0 (Linux; Android 14) Mobile Chrome/119.0",
        ]
        test_referers = [
            "https://google.com/", "https://t.me/", "",
            "https://twitter.com/", "https://yandex.ru/",
        ]

        total = 0
        now = datetime.now(timezone.utc)
        for link in links:
            link_id = link["id"]
            # 5–40 кликов на ссылку, распределённых по дням
            n_clicks = random.randint(5, 40)
            for _ in range(n_clicks):
                day_offset = random.randint(0, days - 1)
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                clicked = now - timedelta(days=day_offset, hours=hour, minutes=minute)
                clicked_at = clicked.strftime("%Y-%m-%dT%H:%M:%SZ")
                conn.execute(
                    """
                    INSERT INTO clicks (
                        link_id, clicked_at, ip_address, user_agent, referer, is_test
                    ) VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (
                        link_id,
                        clicked_at,
                        random.choice(test_ips),
                        random.choice(test_agents),
                        random.choice(test_referers),
                    ),
                )
                total += 1
        conn.commit()
    finally:
        conn.close()

    return {"clicks_created": total, "days": days}


def clear_test_data() -> dict:
    """Удаляет только записи с is_test = 1. Перед этим — бэкап БД."""
    backup_path = _backup_db()
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM clicks WHERE is_test = 1")
        conn.commit()
        deleted = cur.rowcount
    finally:
        conn.close()
    return {"deleted": deleted, "backup": backup_path}
