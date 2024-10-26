# core/models/chat.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey  # Импортируйте ForeignKey
from .base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .message import Message

class Chat(Base):
    __tablename__ = "chats"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)  # Добавлен ForeignKey
    user: Mapped["User"] = relationship("User", back_populates="chats")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat")
