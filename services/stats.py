"""
Статистика переходов, CSV, топ referer'ов.
"""
from __future__ import annotations
import csv
import io
from datetime import datetime, timedelta, timezone

from database.db import get_connection


def record_click(
    link_id: int,
    ip_address: str,
    user_agent: str | None,
    referer: str | None,
    is_test: bool = False,
) -> None:
    """Записывает переход по ссылке."""
    clicked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO clicks (link_id, clicked_at, ip_address, user_agent, referer, is_test)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (link_id, clicked_at, ip_address, user_agent, referer, 1 if is_test else 0),
        )
        conn.commit()
    finally:
        conn.close()


def stats_by_day(link_id: int, days: int = 30) -> list:
    """Визиты по дням за последние N дней (без тестовых)."""
    since = (datetime.now(timezone.utc) - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT date(clicked_at) AS day, COUNT(*) AS count
            FROM clicks
            WHERE link_id = ? AND is_test = 0 AND date(clicked_at) >= ?
            GROUP BY date(clicked_at)
            ORDER BY day
            """,
            (link_id, since),
        ).fetchall()
        counts_map = {r["day"]: r["count"] for r in rows}

        # Заполняем все дни нулями для непрерывного графика
        result = []
        start = datetime.now(timezone.utc) - timedelta(days=days - 1)
        for i in range(days):
            d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            result.append({"day": d, "count": counts_map.get(d, 0)})
        return result
    finally:
        conn.close()


def top_referers(link_id: int, limit: int = 10) -> list:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT COALESCE(NULLIF(referer, ''), '(прямой переход)') AS referer,
                   COUNT(*) AS count
            FROM clicks
            WHERE link_id = ? AND is_test = 0
            GROUP BY referer
            ORDER BY count DESC
            LIMIT ?
            """,
            (link_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def clicks_total_today() -> int:
    """Все клики за сегодня (для дашборда админки)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM clicks
            WHERE is_test = 0 AND date(clicked_at) = ?
            """,
            (today,),
        ).fetchone()
        return row["c"] if row else 0
    finally:
        conn.close()


def clicks_for_link_csv(link_id: int) -> str:
    """CSV всех переходов по одной ссылке."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT clicked_at, ip_address, user_agent, referer, is_test
            FROM clicks WHERE link_id = ?
            ORDER BY clicked_at DESC
            """,
            (link_id,),
        ).fetchall()
    finally:
        conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["clicked_at", "ip_address", "user_agent", "referer", "is_test"])
    for r in rows:
        writer.writerow([
            r["clicked_at"], r["ip_address"], r["user_agent"] or "",
            r["referer"] or "", r["is_test"],
        ])
    return output.getvalue()


def export_all_csv() -> str:
    """CSV всей статистики по всем ссылкам."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT l.slug, l.original_url, c.clicked_at, c.ip_address,
                   c.user_agent, c.referer, c.is_test
            FROM clicks c
            JOIN links l ON l.id = c.link_id
            ORDER BY c.clicked_at DESC
            """
        ).fetchall()
    finally:
        conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "slug", "original_url", "clicked_at", "ip_address",
        "user_agent", "referer", "is_test",
    ])
    for r in rows:
        writer.writerow([
            r["slug"], r["original_url"], r["clicked_at"], r["ip_address"],
            r["user_agent"] or "", r["referer"] or "", r["is_test"],
        ])
    return output.getvalue()
