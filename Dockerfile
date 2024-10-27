# Используем официальный образ Python с поддержкой CUDA
FROM nvidia/cuda:11.7.0-cudnn8-runtime-ubuntu22.04

# Устанавливаем зависимости системы
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-rus \
    netcat \
    && rm -rf /var/lib/apt/lists/*

# Обновляем альтернативы для Python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем pip
RUN python -m pip install --upgrade pip

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Копируем скрипт ожидания
COPY wait-for-it.sh /app/wait-for-it.sh
RUN chmod +x /app/wait-for-it.sh

# Копируем скрипт entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Указываем, что контейнер использует GPU
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Определяем команду по умолчанию
CMD ["./entrypoint.sh"]
