# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.logger import setup_logger
from app.database.vector_store import get_vectorstore
from app.chunks_creating import documents
from app.services.model_loader import ModelLoader  # Импортируем ModelLoader
from app.chunks_creating import create_annotated_documents, create_bm25_index
from app.state import app_state  # Импортируйте app_state
import asyncio

# Инициализация логгера
logger = setup_logger("app")

# Создание экземпляра FastAPI
app = FastAPI(
    title="CILALLM API",
    description="API для управления чатами и сообщениями с поддержкой изображений",
    version="1.0.0",
)

# ...

origins = [
    "http://localhost:3000",
    "https://your-domain.com",
    # Добавьте другие разрешённые источники
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешённые источники
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Инициализация ModelLoader при запуске
@app.on_event("startup")
async def startup_event():
    logger.info("Инициализация модели Qwen2 VL 7b...")
    model_loader = ModelLoader()
    app.state.model_loader = model_loader  # Сохраняем модель в состоянии приложения
    logger.info("Сервер запускается...")

    # Получение аннотированных документов
    annotated_documents = await create_annotated_documents()

    # Разделение для vectorstore и BM25
    vector_documents = [doc for doc in annotated_documents if doc.page_content != doc.metadata['content']]
    bm25_documents = [doc for doc in annotated_documents if doc.page_content == doc.metadata['content']]

    # Индексация в vectorstore
    vectorstore = get_vectorstore()
    await vectorstore.aadd_documents(documents=vector_documents)

    # Создание BM25 индекс
    bm25_documents, bm25 = create_bm25_index(bm25_documents)

    # Сохранение BM25 индекс и документы в app_state
    app_state.bm25 = bm25
    app_state.bm25_documents = bm25_documents

    logger.info("Индексация завершена")
    # Здесь можно добавить инициализацию ресурсов, подключение к другим сервисам и т.д.

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Сервер останавливается...")
    # Очистка ресурсов, закрытие соединений и т.д.
