# Запасной вариант сборки, если Nixpacks снова упадёт (Railway поддерживает Dockerfile)
FROM python:3.11-slim

WORKDIR /app

# Копируем исходники
COPY . .

# Каталог для SQLite (Volume монтируется в /app/data на Railway)
RUN mkdir -p /app/data/backups

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["python3", "app.py"]
