"""
Настройки SuperLinker — читаются из переменных окружения.
Локально можно создать файл .env (не коммитится) или export в shell.
"""
import os
from pathlib import Path

# Корень проекта
BASE_DIR = Path(__file__).resolve().parent

# Порт (Railway задаёт PORT автоматически)
PORT = int(os.environ.get("PORT", "5000"))

# Путь к SQLite: локально ./data/, на Railway — Volume /app/data/
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    str(BASE_DIR / "data" / "superlinker.db"),
)

# Публичный URL сервиса — для отображения коротких ссылок
BASE_URL = os.environ.get("BASE_URL", f"http://localhost:{PORT}").rstrip("/")

# Пароль админки — только через env (Railway Variables)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

# Лимит создания ссылок с одного IP в сутки
RATE_LIMIT_PER_DAY = int(os.environ.get("RATE_LIMIT_PER_DAY", "10"))

# Максимальная длина исходного URL
MAX_URL_LENGTH = int(os.environ.get("MAX_URL_LENGTH", "2048"))

# Максимальная длина кастомного slug
MAX_SLUG_LENGTH = int(os.environ.get("MAX_SLUG_LENGTH", "128"))

# Длина случайного slug по умолчанию
DEFAULT_SLUG_LENGTH = 6

# Имя cookie сессии админки
SESSION_COOKIE = "sl_admin_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 дней

# Зарезервированные slug — нельзя использовать как короткий код
RESERVED_SLUGS = frozenset({
    "admin", "api", "health", "static", "shorten", "login",
    "favicon.ico", "robots.txt",
})
