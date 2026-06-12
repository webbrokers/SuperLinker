"""
Создание и поиск коротких ссылок, редирект с UTM.
"""
from __future__ import annotations
import random
import string
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import config
from database.db import get_connection


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_random_slug(length: int = config.DEFAULT_SLUG_LENGTH) -> str:
    """Генерирует случайный slug из букв и цифр."""
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def is_slug_reserved(slug: str) -> bool:
    return slug.lower() in config.RESERVED_SLUGS


def slug_exists(slug: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute("SELECT 1 FROM links WHERE slug = ?", (slug,)).fetchone()
        return row is not None
    finally:
        conn.close()


def create_link(
    original_url: str,
    custom_slug: Optional[str] = None,
    expires_at: Optional[str] = None,
    title: Optional[str] = None,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    utm_campaign: Optional[str] = None,
) -> dict:
    """
    Создаёт запись ссылки. Возвращает dict с полями link.
    Raises ValueError при ошибках валидации.
    """
    if custom_slug:
        slug = custom_slug.strip()
        if not slug:
            raise ValueError("Кастомный код не может быть пустым")
        if len(slug) > config.MAX_SLUG_LENGTH:
            raise ValueError(f"Код слишком длинный (макс. {config.MAX_SLUG_LENGTH})")
        if is_slug_reserved(slug):
            raise ValueError("Этот код зарезервирован системой")
        if slug_exists(slug):
            raise ValueError("Такой код уже занят")
    else:
        # Подбираем уникальный случайный slug
        for _ in range(20):
            slug = generate_random_slug()
            if not slug_exists(slug):
                break
        else:
            raise ValueError("Не удалось сгенерировать уникальный код")

    created_at = _utc_now_iso()
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO links (
                slug, original_url, created_at, expires_at, title,
                utm_source, utm_medium, utm_campaign
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slug, original_url, created_at, expires_at, title,
                utm_source, utm_medium, utm_campaign,
            ),
        )
        conn.commit()
        link_id = cur.lastrowid
    finally:
        conn.close()

    return {
        "id": link_id,
        "slug": slug,
        "original_url": original_url,
        "created_at": created_at,
        "expires_at": expires_at,
        "short_url": f"{config.BASE_URL}/{slug}",
    }


def get_link_by_slug(slug: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM links WHERE slug = ?", (slug,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_link_by_id(link_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM links WHERE id = ?", (link_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_all_links() -> list:
    """Все ссылки с количеством кликов (без тестовых)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT l.*,
                   COUNT(CASE WHEN c.is_test = 0 THEN 1 END) AS click_count
            FROM links l
            LEFT JOIN clicks c ON c.link_id = l.id
            GROUP BY l.id
            ORDER BY l.created_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def is_link_expired(link: dict) -> bool:
    expires_at = link.get("expires_at")
    if not expires_at:
        return False
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > exp
    except ValueError:
        return False


def build_redirect_url(link: dict) -> str:
    """Собирает URL редиректа с UTM-метками, если заданы."""
    url = link["original_url"]
    utm_params = {}
    if link.get("utm_source"):
        utm_params["utm_source"] = link["utm_source"]
    if link.get("utm_medium"):
        utm_params["utm_medium"] = link["utm_medium"]
    if link.get("utm_campaign"):
        utm_params["utm_campaign"] = link["utm_campaign"]
    if not utm_params:
        return url

    parsed = urlparse(url)
    existing = dict(parse_qsl(parsed.query, keep_blank_values=True))
    existing.update(utm_params)
    new_query = urlencode(existing)
    return urlunparse(parsed._replace(query=new_query))
