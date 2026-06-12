"""
HTTP-утилиты: парсинг запроса, IP клиента, валидация URL, ответы, шаблоны.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote_plus, urlparse

import config

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def get_client_ip(environ) -> str:
    """IP посетителя с учётом прокси Railway (X-Forwarded-For)."""
    forwarded = environ.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return environ.get("REMOTE_ADDR", "0.0.0.0")


def read_body(environ) -> bytes:
    length = int(environ.get("CONTENT_LENGTH") or 0)
    if length <= 0:
        return b""
    return environ["wsgi.input"].read(length)


def parse_form(environ) -> dict:
    """Парсит application/x-www-form-urlencoded или multipart (простой случай)."""
    body = read_body(environ)
    ctype = environ.get("CONTENT_TYPE", "")
    if "application/json" in ctype:
        try:
            return json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    # form-urlencoded
    data = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in data.items()}


def parse_query(environ) -> dict:
    qs = environ.get("QUERY_STRING", "")
    data = parse_qs(qs, keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in data.items()}


def is_valid_url(url: str) -> tuple[bool, str]:
    """Проверяет безопасность и формат URL."""
    url = url.strip()
    if not url:
        return False, "URL не может быть пустым"
    if len(url) > config.MAX_URL_LENGTH:
        return False, f"URL слишком длинный (макс. {config.MAX_URL_LENGTH})"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "Разрешены только ссылки http:// и https://"
    if not parsed.netloc:
        return False, "Некорректный URL"
    lower = url.lower()
    if lower.startswith("javascript:") or lower.startswith("data:"):
        return False, "Недопустимый тип ссылки"
    # Блокировка localhost / private IP в hostname (базовая защита)
    host = parsed.hostname or ""
    if re.match(r"^(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)", host):
        return False, "Нельзя сокращать внутренние адреса"
    return True, ""


def parse_expires_days(days_str: str) -> str | None:
    """Преобразует '1', '7', '30' в ISO datetime UTC или None."""
    if not days_str or days_str == "0":
        return None
    from datetime import datetime, timedelta, timezone
    try:
        days = int(days_str)
        if days <= 0:
            return None
        exp = datetime.now(timezone.utc) + timedelta(days=days)
        return exp.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def render_template(name: str, **context) -> str:
    """Подставляет {{key}} в HTML-шаблон."""
    path = TEMPLATES_DIR / name
    html = path.read_text(encoding="utf-8")
    for key, value in context.items():
        html = html.replace("{{" + key + "}}", str(value))
    return html


def html_response(body: str, status: str = "200 OK", headers: dict | None = None) -> tuple:
    h = [("Content-Type", "text/html; charset=utf-8")]
    if headers:
        h.extend(headers.items())
    return status, h, body.encode("utf-8")


def json_response(data: dict, status: str = "200 OK") -> tuple:
    body = json.dumps(data, ensure_ascii=False)
    return status, [("Content-Type", "application/json; charset=utf-8")], body.encode("utf-8")


def redirect_response(location: str, status: str = "302 Found") -> tuple:
    return status, [("Location", location)], b""


def csv_response(content: str, filename: str) -> tuple:
    headers = [
        ("Content-Type", "text/csv; charset=utf-8"),
        ("Content-Disposition", f'attachment; filename="{filename}"'),
    ]
    return "200 OK", headers, content.encode("utf-8-sig")


def static_file_response(path: str) -> tuple | None:
    """Отдаёт файл из static/ или None если не найден."""
    rel = path.lstrip("/")
    if not rel.startswith("static/"):
        return None
    file_path = Path(__file__).resolve().parent.parent / rel
    if not file_path.is_file():
        return None
    suffix = file_path.suffix.lower()
    mime = {
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".ico": "image/x-icon",
    }.get(suffix, "application/octet-stream")
    return "200 OK", [("Content-Type", mime)], file_path.read_bytes()


def wsgi_response(result: tuple):
    """Оборачивает (status, headers, body) в WSGI callable."""
    status, headers, body = result

    def start_response(status_line, response_headers, exc_info=None):
        pass

    return [body]
