# SuperLinker

Сервис сокращения ссылок с аналитикой переходов.

## Документация

| Файл | Описание |
|------|----------|
| [docs/ПРАВИЛА-ПРОЕКТА.md](docs/ПРАВИЛА-ПРОЕКТА.md) | Правила работы |
| [docs/ПЛАН-ДЕЙСТВИЙ.md](docs/ПЛАН-ДЕЙСТВИЙ.md) | План MVP |
| [docs/DEPLOY-RAILWAY.md](docs/DEPLOY-RAILWAY.md) | Деплой на Railway |
| [docs/DESIGN.md](docs/DESIGN.md) | UI и стиль |
| [docs/ЖУРНАЛ-ИЗМЕНЕНИЙ.md](docs/ЖУРНАЛ-ИЗМЕНЕНИЙ.md) | Журнал изменений |

## Локальный запуск

```bash
cp .env.example .env
# Отредактируйте ADMIN_PASSWORD в .env

python3 app.py
```

Откройте http://localhost:5000

## Railway

1. Push в GitHub
2. Railway → New Project → GitHub → SuperLinker
3. Volume: mount `/app/data`
4. Variables:
   - `DATABASE_PATH=/app/data/superlinker.db`
   - `BASE_URL=https://ваш-url.up.railway.app`
   - `ADMIN_PASSWORD=ваш_пароль`
   - `RATE_LIMIT_PER_DAY=10`
5. Deploy

Подробнее: [docs/DEPLOY-RAILWAY.md](docs/DEPLOY-RAILWAY.md)

## Стек

Python 3 (stdlib) · SQLite · vanilla JS/CSS · без pip/npm
