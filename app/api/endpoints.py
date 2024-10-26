# app/api/endpoints.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import photo_indexes
from ...core.models.crud import (
    create_user,
    get_user_by_user_id,
    create_chat,
    create_message,
    get_chat_history,
)
from ...core.models.db_helper import db_helper
from ...core.models.chat import Chat
from ..graphs.main_graph import worker  # Предполагается, что worker доступен из llm.py
from ..schemas.state import State
from langchain.schema import Document
from ..schemas.chat import ChatHistoryResponse
from ..schemas.message import SendMessageResponse
from PIL import Image
import pytesseract
from datetime import datetime
import os

router = APIRouter()

@router.post("/upload_history")
async def upload_history(user_id: str, history: List[dict], session: AsyncSession = Depends(db_helper.session_dependency)):
    user = await get_user_by_user_id(session, user_id)
    if not user:
        user = await create_user(session, user_id)
    chat = await create_chat(session, user)
    for msg in history:
        await create_message(session, chat, msg['sender'], msg['content'])
    return {"status": "success", "chat_id": chat.id}

@router.get("/chat_history/{chat_id}", response_model=ChatHistoryResponse)
async def chat_history(chat_id: int, session: AsyncSession = Depends(db_helper.session_dependency)):
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = await get_chat_history(session, chat)
    return ChatHistoryResponse(messages=[{"sender": msg.sender, "content": msg.content, "timestamp": msg.timestamp} for msg in messages])

@router.post("/send_message", response_model=SendMessageResponse)
async def send_message(
    user_id: str,
    chat_id: int,
    message: str,
    files: List[UploadFile] = File(None),
    session: AsyncSession = Depends(db_helper.session_dependency)
):
    # Проверка пользователя
    user = await get_user_by_user_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверка чата
    chat = await session.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Обработка файлов (фото)
    image_texts = []
    if files:
        for file in files:
            if file.content_type.startswith("image/"):
                file_path = os.path.join("uploads", file.filename)
                os.makedirs("uploads", exist_ok=True)
                async with aiofiles.open(file_path, 'wb') as out_file:
                    content = await file.read()
                    await out_file.write(content)
                
                # Конвертация изображения в текст с помощью OCR
                try:
                    img = Image.open(file_path)
                    text = pytesseract.image_to_string(img, lang='rus')  # Предполагается, что текст на русском
                    image_texts.append(text)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Ошибка обработки изображения: {e}")

    # Комбинирование текста сообщения и текста из изображений
    combined_message = message + "\n" + "\n".join(image_texts) if image_texts else message
    
    # Сохранение сообщения пользователя в базе данных
    user_message = await create_message(session, chat, "user", combined_message)
    
    # Получение последних 6 сообщений из истории чата
    last_messages_objs = await get_last_messages(session, chat, limit=5)  # Последние 5 сообщений до текущего
    # Формирование списка кортежей (sender, content)
    last_messages = [(msg.sender, msg.content) for msg in last_messages_objs]
    # Добавление текущего сообщения пользователя
    last_messages.append(("user", combined_message))
    
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
    
    # Вызов worker
    try:
        response_state = await worker.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при вызове worker: {e}")
    
    # Сохранение ответа бота в базе данных
    bot_answer = response_state.get("answer", "")
    await create_message(session, chat, "bot", bot_answer)
    
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
                    photos_info.append({
                        "chapter": chapter_num,
                        "image_number": image_num,
                        "path": path
                    })
    
    return SendMessageResponse(
        user_message=user_message.content,
        bot_answer=bot_answer,
        photos=photos_info
    )