from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime
from datetime import datetime, timezone
from auth.models import Base
from typing import List

class MessageModel(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(2048), default="")
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))

    chat_msg: Mapped["ChatModel"] = relationship(back_populates="messages")
    

class ChatModel(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(primary_key=True)
    is_group: Mapped[bool] = mapped_column(default=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=timezone.utc), default=lambda: datetime.now(timezone.utc))
    direct_key: Mapped[str | None] = mapped_column(String(100), unique=True, default=None)

    participants: Mapped[List["ParticipantsModel"]] = relationship(back_populates="chat")
    messages: Mapped[List["MessageModel"]] = relationship(back_populates="chat_msg")

class ParticipantsModel(Base):
    __tablename__ = "participants"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    chat: Mapped["ChatModel"] = relationship(back_populates="participants")
    # когда наконец таки закончу с проектированием бд, надо вебсокеты реализовать
    # когда будет свободное время: сделать в auth у ручек status коды для успешного возврата