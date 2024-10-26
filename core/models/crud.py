# core/models/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
from .user import User
from .chat import Chat
from .message import Message

from ...app.schemas.chat import ChatWithLastMessageResponse, LastMessageSchema

async def create_user(session: AsyncSession, user_id: str) -> User:
    user = User(user_id=user_id)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_user_id(session: AsyncSession, user_id: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()

async def create_chat(session: AsyncSession, user: User) -> Chat:
    chat = Chat(user_id=user.id)
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat

async def create_message(session: AsyncSession, chat: Chat, sender: str, content: str) -> Message:
    message = Message(chat_id=chat.id, sender=sender, content=content)
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message

async def get_last_five_chats_with_last_message(session: AsyncSession, user_id: str, limit: int = 5) -> List[ChatWithLastMessageResponse]:
    """
    Получает последние пять чатов пользователя вместе с последним сообщением в каждом чате.
    """
    # Подзапрос для получения времени последнего сообщения в каждом чате
    subquery = (
        select(
            Message.chat_id,
            func.max(Message.timestamp).label("last_message_time")
        )
        .join(Chat, Chat.id == Message.chat_id)
        .join(User, User.id == Chat.user_id)
        .where(User.user_id == user_id)
        .group_by(Message.chat_id)
        .subquery()
    )
    
    # Основной запрос для получения чатов и их последних сообщений
    stmt = (
        select(Chat, Message)
        .join(subquery, Chat.id == subquery.c.chat_id)
        .join(Message, (Message.chat_id == Chat.id) & (Message.timestamp == subquery.c.last_message_time))
        .order_by(desc(subquery.c.last_message_time))
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    rows = result.fetchall()
    
    chats_with_last_messages = []
    for chat, message in rows:
        last_message = LastMessageSchema(
            sender=message.sender,
            content=message.content,
            timestamp=message.timestamp
        )
        chat_response = ChatWithLastMessageResponse(
            chat_id=chat.id,
            last_message=last_message
        )
        chats_with_last_messages.append(chat_response)
    
    return chats_with_last_messages

async def get_last_n_messages(session: AsyncSession, chat: Chat, limit: int = 5) -> List[Message]:
    """
    Получает последние N сообщений из чата.
    """
    stmt = select(Message).where(Message.chat_id == chat.id).order_by(desc(Message.timestamp)).limit(limit)
    result = await session.execute(stmt)
    messages = result.scalars().all()
    return list(reversed(messages))  # Возвращаем в хронологическом порядке
