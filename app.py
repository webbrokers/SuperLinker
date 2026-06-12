"""
Точка входа SuperLinker — WSGI-приложение на stdlib.
Запуск: python app.py
"""
import os
from wsgiref.simple_server import make_server

import config
from database import init_db
from server.router import dispatch


def application(environ, start_response):
    """WSGI entry point для Railway и локального запуска."""
    try:
        return dispatch(environ, start_response)
    except Exception:
        start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
        return [b"Internal Server Error"]


def main():
    # Локально подхватываем .env без сторонних библиотек
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.isfile(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

    # Перечитываем config после .env
    import importlib
    importlib.reload(config)

    init_db()
    host = "0.0.0.0"
    port = config.PORT
    print(f"SuperLinker запущен: {config.BASE_URL} (port {port})")
    with make_server(host, port, application) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
