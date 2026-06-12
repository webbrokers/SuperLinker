"""
Схема SQLite и первичная инициализация таблиц.
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    original_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    title TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT
);

CREATE TABLE IF NOT EXISTS clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id INTEGER NOT NULL,
    clicked_at TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    referer TEXT,
    is_test INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (link_id) REFERENCES links(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rate_limits (
    ip_address TEXT NOT NULL,
    day TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (ip_address, day)
);

CREATE INDEX IF NOT EXISTS idx_clicks_link_id ON clicks(link_id);
CREATE INDEX IF NOT EXISTS idx_clicks_clicked_at ON clicks(clicked_at);
CREATE INDEX IF NOT EXISTS idx_links_slug ON links(slug);
"""


def init_schema(conn) -> None:
    """Создаёт таблицы, если их ещё нет."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
