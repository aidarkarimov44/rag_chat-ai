# core/models/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .user import User
from .chat import Chat
from .message import Message
from typing import List

async def create_user(session: AsyncSession, user_id: str) -> User:
    user = User(user_id=user_id)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_user_id(session: AsyncSession, user_id: str) -> User | None:
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

async def get_chat_history(session: AsyncSession, chat: Chat) -> list[Message]:
    result = await session.execute(select(Message).where(Message.chat_id == chat.id).order_by(Message.timestamp))
    return result.scalars().all()

async def get_last_messages(session: AsyncSession, chat: Chat, limit: int = 6) -> List[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.chat_id == chat.id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return list(reversed(messages))  # Вернуть в хронологическом порядке