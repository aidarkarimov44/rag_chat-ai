# app/api/endpoints.py
import base64
import os
import uuid
from io import BytesIO
from typing import List

import aiofiles
from fastapi import APIRouter, Depends, HTTPException
from pytesseract import pytesseract
from sqlalchemy.ext.asyncio import AsyncSession
from yandex.cloud.ai.vision.v2.image_pb2 import Image

from core.models import User, Chat
from ..graphs.main_graph import worker
from ..schemas.chat import ChatWithLastMessageResponse
from ..schemas.message import GetMessageHistoryResponse, PhotoInfo, SendMessageResponse, SendMessageRequest
from ..schemas.state import State
from ..schemas.user import UserResponse
from ...core.models.crud import (
    create_user,
    create_chat,
    get_user_by_user_id,
    get_last_five_chats_with_last_message,
    get_all_chat_history_by_chat_id, create_message, get_last_n_messages
)
from ...core.models.db_helper import db_helper
from ..dependencies import get_model_loader  # Импортируем зависимость

router = APIRouter()

@router.get("/chat_history/{chat_id}", response_model=List[GetMessageHistoryResponse])
async def get_chat_history(chat_id: str, session: AsyncSession = Depends(db_helper.session_dependency)):
    messages = await get_all_chat_history_by_chat_id(session, int(chat_id))
    message_responses = []
    for i in messages:
        message_responses.append(
            GetMessageHistoryResponse(
                sender=i.sender,
                content=i.content,
                timestamp=str(i.timestamp)
            )
        )
    return message_responses

@router.post("/chat-create/{user_id}")
async def create_chat_post(user_id: str, session: AsyncSession = Depends(db_helper.session_dependency)):
    chat = await create_chat(session, User(id=int(user_id)))
    return {"chat_id" : str(chat.id)}

@router.post("/user", response_model=UserResponse)
async def new_user(session: AsyncSession = Depends(db_helper.session_dependency)):
    """
    Создает нового пользователя с уникальным user_id.
    """
    try:
        # Генерация нового UUID
        new_uuid = str(uuid.uuid4())
        new_user = await create_user(session=session, user_id=new_uuid)
        return UserResponse(user_id=str(new_user.id))
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
        user = await get_user_by_user_id(session, int(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Получаем последние пять чатов с последними сообщениями
        chats_with_messages = await get_last_five_chats_with_last_message(session, int(user_id), limit=5)
        return chats_with_messages
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send_message", response_model=SendMessageResponse)
async def send_message(
        request: SendMessageRequest,
        session: AsyncSession = Depends(db_helper.session_dependency),
        model_loader: ModelLoader = Depends(get_model_loader)  # Подключаем зависимость
):
    """
    Отправляет сообщение пользователем в чат и возвращает ответ от бота.
    Поддерживает отправку изображений в формате Base64 с использованием модели Qwen для извлечения текста.
    """
    user_id = request.user_id
    chat_id = request.chat_id
    message = request.message
    images = request.images

    # Проверка существования пользователя
    user = await get_user_by_user_id(session, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверка существования чата
    chat = await session.get(Chat, int(chat_id))
    if not chat:
        chat = await create_chat(session, user)

    # Обработка отправленных изображений с использованием Qwen
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

                # Использование модели Qwen для извлечения текста из изображения
                processor = model_loader.get_processor()
                model = model_loader.get_model()

                # Подготовка сообщений для модели Qwen
                messages_qwen = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "image": file_path,  # Используем локальный путь к сохраненному изображению
                            },
                            {"type": "text", "text": "Describe this image."},
                        ],
                    }
                ]

                # Подготовка к инференсу
                text = processor.apply_chat_template(
                    messages_qwen, tokenize=False, add_generation_prompt=True
                )
                image_inputs, video_inputs = process_vision_info(messages_qwen)
                inputs = processor(
                    text=[text],
                    images=image_inputs,
                    videos=video_inputs,
                    padding=True,
                    return_tensors="pt",
                )

                # Переносим данные на GPU
                inputs = {k: v.to(model.device) for k, v in inputs.items() if isinstance(v, torch.Tensor)}

                # Инференс: Генерация ответа
                with torch.no_grad():
                    generated_ids = model.generate(**inputs, max_new_tokens=128)
                generated_ids_trimmed = [
                    out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
                ]
                output_text = processor.batch_decode(
                    generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
                )

                image_texts.append(output_text[0])  # Добавляем сгенерированный текст

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
    try:
        response_state = await worker.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при вызове worker: {e}")

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
                        async with aiofiles.open(path, "rb") as image_file:
                            image_bytes = await image_file.read()
                            encoded_string = base64.b64encode(image_bytes).decode('utf-8')
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
        chat_id=chat.id,
        photos=photos_info
    )