CILALLM API и Frontend Chatbot Sila AI
Добро пожаловать в репозиторий CILALLM API и Frontend Chatbot Sila AI! Этот проект состоит из двух основных частей:

Backend: API на базе FastAPI для управления чатами и сообщениями с поддержкой изображений.
Frontend: Простое React-приложение на TypeScript с использованием Vite для интерфейса чатбота.
Содержание
О проекте
Структура проекта
Предварительные требования
Установка и запуск
Клонирование репозитория
Настройка окружения
Сборка и запуск с помощью Docker Compose
Использование фронтенда
Решение распространённых ошибок
Вклад
Лицензия
О проекте
CILALLM API — это API на базе FastAPI, предназначенное для управления пользователями, чатами и сообщениями с поддержкой изображений. API интегрируется с моделями машинного обучения для обработки сообщений и генерации ответов.

Frontend Chatbot Sila AI — это фронтенд-приложение на React с использованием TypeScript и Vite, предоставляющее интерфейс для общения с чатботом.

Структура проекта

├── backend/                     # FastAPI проект
│   ├── Dockerfile
│   ├── alembic/                
│   ├── app/
│   │   ├── api/
│   │   ├── chunks_creating.py
│   │   ├── config.py
│   │   ├── database/
│   │   ├── dependencies.py
│   │   ├── graphs/
│   │   ├── logger.py
│   │   ├── main.py
│   │   ├── photo_indexes.py
│   │   ├── preprocessing/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── state.py
│   ├── core/
│   ├── docker-compose.yml
│   ├── entrypoint.sh
│   ├── images/
│   ├── logs/
│   ├── requirements.txt
│   ├── uploads/
│   └── wait-for-it.sh
├── frontend/                    # React приложение на Vite
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   └── public/
├── nginx/
│   └── conf.d/
│       └── default.conf
├── docker-compose.yml          # Основной файл Docker Compose
└── README.md
Предварительные требования
Для успешной установки и запуска проекта убедитесь, что у вас установлены следующие инструменты:

Docker (рекомендуемая версия 20.10 или выше)
Docker Compose (входит в состав Docker Desktop)
Git (для клонирования репозитория)
Установка и запуск
Клонирование репозитория
Сначала клонируйте репозиторий на вашу локальную машину:

bash

git clone https://github.com/ваш-логин/ваш-репозиторий.git
cd ваш-репозиторий
Настройка окружения
Backend:

Создайте файл .env в директории backend/ и добавьте необходимые переменные окружения:

env

# backend/.env

YANDEXGPT_IAM_TOKEN=your_yandex_iam_token
YANDEXGPT_MODEL_URI=your_yandex_model_uri
YANDEXGPT_MAIN_MODEL_URI=your_main_model_uri
EMBEDDINGS_MODEL=your_embeddings_model
DEVICE=your_device_settings
PG_CONNECTION=postgresql://postgres:postgres@db:5432/cilallm
PG_COLLECTION_NAME=your_pg_collection_name
GIGACHAT_CREDENTIALS=your_gigachat_credentials
Примечание: Замените your_* на ваши актуальные значения.

Frontend:

Создайте файл .env в директории frontend/ и добавьте переменные окружения:

env

# frontend/.env

VITE_API_URL=/api
Это позволит вашему React-приложению направлять API-запросы на бэкенд.

Сборка и запуск с помощью Docker Compose
В корневой директории проекта выполните следующие команды для сборки и запуска всех сервисов:

bash

docker-compose build
docker-compose up -d
Эти команды выполнят следующие действия:

db: Запустит PostgreSQL с расширением pgvector.
backend: Соберет и запустит FastAPI-приложение.
frontend: Соберет и запустит React-приложение.
nginx: Настроит Nginx для обслуживания фронтенда и проксирования API-запросов к бэкенду.
Использование фронтенда
После успешного запуска всех сервисов, ваш фронтенд будет доступен по адресу:


http://localhost
Этот интерфейс позволит вам взаимодействовать с чатботом Sila AI. Для разработки вы также можете открыть отдельный сервис на порту 3000:


http://localhost:3000
Решение распространённых ошибок
Ошибка циклического импорта
Описание ошибки:


ImportError: cannot import name 'app' from partially initialized module 'app.main' (most likely due to a circular import)
Решение:

Эта ошибка возникает из-за циклического импорта между модулями app.main и app.dependencies. Чтобы исправить это, измените способ получения model_loader через Request вместо прямого импорта app.main в app/dependencies.py.

Измените app/dependencies.py:

python

# app/dependencies.py

from fastapi import Depends, Request, HTTPException
from app.services.model_loader import ModelLoader

async def get_model_loader(request: Request) -> ModelLoader:
    model_loader = getattr(request.app.state, "model_loader", None)
    if not model_loader:
        raise HTTPException(status_code=500, detail="Модель ещё не загружена")
    return model_loader
Обновите app/api/endpoints.py для использования новой зависимости:

python

# app/api/endpoints.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..dependencies import get_model_loader  # Импортируем зависимость

router = APIRouter()

@router.post("/send_message", response_model=SendMessageResponse)
async def send_message(
        request: SendMessageRequest,
        session: AsyncSession = Depends(db_helper.session_dependency),
        model_loader: ModelLoader = Depends(get_model_loader)  # Подключаем зависимость
):
    # Ваш код обработки запроса...
Убедитесь, что app/main.py инициализирует model_loader корректно:

python

# app/main.py

from fastapi import FastAPI
# Другие импорты...

app = FastAPI(
    title="CILALLM API",
    description="API для управления чатами и сообщениями с поддержкой изображений",
    version="1.0.0",
)

# Другие настройки...

@app.on_event("startup")
async def startup_event():
    logger.info("Инициализация модели Qwen2 VL 7b...")
    model_loader = ModelLoader()
    app.state.model_loader = model_loader  # Сохраняем модель в состоянии приложения
    # Остальная часть вашего кода...
Ошибка при запуске Docker
Описание ошибки:

Если при запуске Docker вы сталкиваетесь с ошибками, связанными с правами доступа или нехваткой ресурсов, убедитесь, что:

У вас установлены все необходимые драйверы для GPU (если используется).
Порты, указанные в docker-compose.yml, не заняты другими приложениями.
Переменные окружения настроены корректно.
Пример ошибки:


Cannot connect to the Docker daemon. Is the docker daemon running on this host?
Решение:

Запустите Docker сервис:

bash

sudo systemctl start docker
Или, если вы используете Docker Desktop, убедитесь, что он запущен.

Вклад
Мы рады приветствовать вклад сообщества! Если вы нашли ошибку или хотите предложить улучшение, пожалуйста, создайте issue или отправьте pull request.

Лицензия
Этот проект лицензирован под лицензией MIT. Подробнее см. в файле LICENSE.

Если у вас возникли дополнительные вопросы или проблемы, не стесняйтесь обращаться к документации или открывать issue в репозитории.