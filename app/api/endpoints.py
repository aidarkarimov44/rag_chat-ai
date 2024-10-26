# app/api/endpoints.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import aiofiles
import os
from core.models.crud import (
    create_user,
    get_user_by_user_id,
    create_chat,
    create_message,
    get_last_five_chats_with_last_message,
    get_last_n_messages,
)
from core.models.db_helper import db_helper
from core.models.chat import Chat
from ..graphs.main_graph import worker  # Предполагается, что worker доступен из llm.py
from ..schemas.state import State
from ..schemas.chat import ChatWithLastMessageResponse
from ..schemas.message import SendMessageResponse, SendMessageRequest, PhotoInfo
from ..schemas.user import UserCreateResponse
from PIL import Image
import pytesseract
from io import BytesIO
import base64
from datetime import datetime

router = APIRouter()

@router.post("/user", response_model=UserCreateResponse)
async def new_user(session: AsyncSession = Depends(db_helper.session_dependency)):
    """
    Создает нового пользователя с уникальным user_id.
    """
    try:
        # Генерация нового UUID
        new_uuid = str(uuid.uuid4())
        new_user = await create_user(session=session, user_id=new_uuid)
        return UserCreateResponse(user_id=new_user.user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/last/{user_id}", response_model=List[ChatWithLastMessageResponse])
async def get_last_five_chat_by_id(
        user_id: str,
        session: AsyncSession = Depends(db_helper.session_dependency)
):
    """
    Получает последние пять чатов пользователя идентификатора user_id.
    """
    try:
        # Проверяем существование пользователя
        user = await get_user_by_user_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Получаем последние пять чатов с последними сообщениями
        chats_with_messages = await get_last_five_chats_with_last_message(session, user_id, limit=5)
        return chats_with_messages
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send_message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    session: AsyncSession = Depends(db_helper.session_dependency)
):
    """
    Отправляет сообщение пользователем в чат и возвращает ответ от бота.
    Поддерживает отправку изображений в формате Base64.
    """
    user_id = request.user_id
    chat_id = request.chat_id
    message = request.message
    images = request.images

    # Проверка существования пользователя
    user = await get_user_by_user_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Попытка получить чат
    chat = await session.get(Chat, chat_id)
    
    # Если чат не найден, создаем новый чат для пользователя
    if not chat:
        try:
            chat = await create_chat(session, user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка создания нового чата: {e}")
    
    # Обработка отправленных изображений (Base64)
    image_texts = []
    if images:
        for img in images:
            try:
                # Декодирование Base64 в байты
                image_data = base64.b64decode(img.data)
                
                # Сохранение изображения на сервер
                file_path = os.path.join("uploads", img.filename)
                os.makedirs("uploads", exist_ok=True)
                async with aiofiles.open(file_path, 'wb') as out_file:
                    await out_file.write(image_data)
                
                # Конвертация изображения в текст с помощью OCR
                img_pil = Image.open(BytesIO(image_data))
                text = pytesseract.image_to_string(img_pil, lang='rus')  # Предполагаем, что текст на русском
                image_texts.append(text)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка обработки изображения {img.filename}: {e}")

    # Комбинирование текста сообщения и текста из изображений
    if image_texts:
        combined_message = f"{message}\n" + "\n".join(image_texts)
    else:
        combined_message = message
    
    # Сохранение сообщения пользователя в базе данных
    try:
        await create_message(session, chat, "user", combined_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения сообщения: {e}")
    
    # Получение последних 5 сообщений из чата для контекста
    try:
        last_messages_objs = await get_last_n_messages(session, chat, limit=5)
        # Формирование списка кортежей (sender, content)
        last_messages = [(msg.sender, msg.content) for msg in last_messages_objs]
        # Добавление текущего сообщения пользователя для формирования контекста
        last_messages.append(("user", combined_message))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории чата: {e}")
    
    # Инициализация состояния
    initial_state: State = {
        "user_message": combined_message,
        "last_messages": last_messages,
        "is_index": False,
        "answer": "",
        "rel_docs": [],
        "db_query": "",
        "retries": 0,
        "rewrite": False
    }
    
    # Вызов worker для обработки состояния
    # try:
    #     response_state = await worker.ainvoke(initial_state)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Ошибка при вызове worker: {e}")
    response_state = await worker.ainvoke(initial_state)
    # Получение ответа бота и его сохранение
    bot_answer = response_state.get("answer", "")
    try:
        await create_message(session, chat, "bot", bot_answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения ответа бота: {e}")
    
    # Обработка rel_docs для отправки фотографий
    photos_info = []
    if response_state.get("rel_docs"):
        for doc in response_state["rel_docs"]:
            for chapter, details in doc.items():
                content = details.get("content", "")
                image_paths = details.get("paths", [])
                for path in image_paths:
                    # Извлечение номера главы и номера рисунка из имени файла
                    filename = os.path.basename(path)
                    parts = filename.split('_')
                    if len(parts) < 2:
                        continue  # Неверный формат имени файла
                    chapter_num = parts[0]
                    image_num_part = parts[1].split('.')[0]  # Пример: 'image1.png' -> 'image1'
                    image_num = ''.join(filter(str.isdigit, image_num_part))  # Извлекаем только цифры
                    
                    # Чтение изображения и кодирование в Base64
                    try:
                        with open(path, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Ошибка чтения изображения {path}: {e}")
                    
                    photos_info.append(PhotoInfo(
                        chapter=chapter_num,
                        image_number=image_num,
                        base64_data=encoded_string
                    ))
    
    return SendMessageResponse(
        user_message=combined_message,
        bot_answer=bot_answer,
        photos=photos_info
    )
