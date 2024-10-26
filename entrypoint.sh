#!/usr/bin/env bash
# entrypoint.sh

# Ожидаем готовности базы данных
./wait-for-it.sh db 5432 --timeout=60 --strict -- echo "База данных доступна"

# Выполняем миграции Alembic
echo "Выполнение миграций базы данных..."
alembic upgrade head

# Запускаем сервер Uvicorn
echo "Запуск сервера..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
