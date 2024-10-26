# core/models/message.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .chat import Chat
class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column()
    sender: Mapped[str] = mapped_column()  # 'user' или 'bot'
    content: Mapped[str] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
