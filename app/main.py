# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.logger import setup_logger
from app.database.vector_store import get_vectorstore
from app.chunks_creating import documents
# Инициализация логгера
logger = setup_logger("app")

# Создание экземпляра FastAPI
app = FastAPI(
    title="CILALLM API",
    description="API для управления чатами и сообщениями с поддержкой изображений",
    version="1.0.0",
)

# Настройка CORS (при необходимости)
# Если ваше приложение будет обращаться из браузера, возможно, потребуется настроить разрешенные источники
origins = [
    "http://localhost",
    "http://localhost:8000",
    # Добавьте другие разрешенные источники
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Разрешенные источники
    allow_credentials=True,
    allow_methods=["*"],              # Разрешенные методы HTTP
    allow_headers=["*"],              # Разрешенные заголовки
)

# Подключение маршрутизатора API с префиксом /api
app.include_router(endpoints.router, prefix="/api")

# Корневой маршрут для проверки работоспособности сервера
@app.get("/")
async def root():
    logger.info("Корневой маршрут был вызван")
    return {"message": "Добро пожаловать в CILALLM API"}

# Пример маршрута для проверки базы данных или других сервисов (по желанию)
@app.get("/health")
async def health_check():
    return {"status": "OK"}

# Обработчики событий запуска и остановки (по необходимости)
@app.on_event("startup")
async def startup_event():
    vectorstore = get_vectorstore()
    await vectorstore.aadd_documents(documents=documents)
    logger.info("Сервер запускается...")
    # Здесь можно добавить инициализацию ресурсов, подключение к другим сервисам и т.д.

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Сервер останавливается...")
    # Здесь можно добавить очистку ресурсов, закрытие соединений и т.д.
