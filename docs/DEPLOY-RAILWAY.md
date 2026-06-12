# Деплой SuperLinker на Railway

> **Статус: согласовано** — вариант A (SQLite + Volume), платная подписка Railway.

---

## 1. Схема

```
GitHub (код)  ──push──►  Railway (Python WSGI)  ──►  Volume: /app/data/superlinker.db
                              │
                              ▼
                    https://ваш-проект.up.railway.app/{slug}
```

| Роль | Платформа |
|------|-----------|
| Код | GitHub |
| Runtime | Railway (Nixpacks → Python 3) |
| БД | SQLite на **Volume** |

---

## 2. Настройка Volume (обязательно)

1. Railway Dashboard → ваш сервис → **Volumes** → Create Volume.
2. Mount path: **`/app/data`**
3. Переменная: `DATABASE_PATH=/app/data/superlinker.db`
4. Если ошибка записи SQLite: добавить `RAILWAY_RUN_UID=0`

Без Volume данные **теряются** при каждом redeploy.

---

## 3. Переменные окружения

| Переменная | Пример | Назначение |
|------------|--------|------------|
| `PORT` | *(Railway)* | Порт сервера |
| `DATABASE_PATH` | `/app/data/superlinker.db` | SQLite на Volume |
| `BASE_URL` | `https://xxx.up.railway.app` | Префикс коротких ссылок |
| `ADMIN_PASSWORD` | *(ваш секрет)* | Пароль админки — **только в Railway, не в Git** |
| `RAILWAY_RUN_UID` | `0` | Права на Volume (при необходимости) |

---

## 4. Запуск без pip-зависимостей

```toml
# railway.toml (план)
[build]
builder = "nixpacks"

[deploy]
startCommand = "python app.py"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
```

Nixpacks определит Python из репозитория. `requirements.txt` не нужен.

---

## 5. IP клиента

Railway проксирует запросы. Берём первый IP из заголовка `X-Forwarded-For`.

---

## 6. Чеклист деплоя

- [ ] Push кода в GitHub
- [ ] New Project → Deploy from GitHub → SuperLinker
- [ ] Volume `/app/data`
- [ ] Variables: `DATABASE_PATH`, `BASE_URL`, `ADMIN_PASSWORD`
- [ ] Deploy → проверить `/health`
- [ ] Сократить ссылку → перейти → проверить статистику

---

*Обновлено: 2026-06-12*
