# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем зависимости системы
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev poppler-utils tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем Tesseract языки (например, русский)
RUN apt-get update && \
    apt-get install -y tesseract-ocr-rus && \
    rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Копируем скрипт ожидания
COPY wait-for-it.sh /app/wait-for-it.sh
RUN chmod +x /app/wait-for-it.sh

# Копируем скрипт entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Определяем команду по умолчанию
CMD ["./entrypoint.sh"]
