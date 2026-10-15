from fastapi import APIRouter, Depends, HTTPException, status
from database import DbSession
from chat.schemas import CreateDirectIn
from auth.auth import get_current_user
from chat.models import ChatModel, ParticipantsModel
from sqlalchemy import select, and_, join, func
from auth.models import UserModel
import asyncio
from sqlalchemy.exc import IntegrityError

chat_router = APIRouter()

@chat_router.post("/chats/direct")
async def create_direct_chat(
    db: DbSession, 
    data: CreateDirectIn, 
    current_user = Depends(get_current_user)):

    # Проверка на чат с самим собой
    if current_user.id == data.user_id:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="You cannot create a chat with yourself"
        )

    # Проверка на существование пользователя для создания чата
    query = select(UserModel).where(UserModel.id == data.user_id)
    res = (await db.execute(query)).scalars().first()

    if not res:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="User you are trying to chat does not exist"
        )

    # Проверка что такого диалога уже не существует
    query = (
        select(ParticipantsModel.chat_id)
        .join(ChatModel, ChatModel.id == ParticipantsModel.chat_id)
        .where(and_(ParticipantsModel.user_id.in_([data.user_id, current_user.id]), ChatModel.is_group == False))
        .group_by(ParticipantsModel.chat_id)
        .having(func.count(ParticipantsModel.user_id) == 2)
    )
           
    res = (await db.execute(query)).scalars().first()

    if res:
        return res

    largest_id = max(current_user.id, data.user_id)
    lowest_id = min(current_user.id, data.user_id)

    new_chat = ChatModel(is_group=False, name=None, direct_key=f"{lowest_id}:{largest_id}")
    # Удалять их не надо, они нужны для того чтоб через relationship автоматически данные в бд добавились
    participant_1 = ParticipantsModel(chat = new_chat, user_id = current_user.id)
    participant_2 = ParticipantsModel(chat = new_chat, user_id = data.user_id)

    # Обработка race condition при 2 запросах на создание личного чата одновременно
    db.add(new_chat)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        query = select(ChatModel).where(ChatModel.direct_key == f"{lowest_id}:{largest_id}")
        res = (await db.execute(query)).scalar()

        if res:
            return res.id

        # если вдруг тут res нулевой, значит ошибка где то есть и raise чтоб она наверх всплыла в таком случае
        raise

    return new_chat.id

# @chat_router.post("/chats/group")
# async def create_group_chat(db:DbSession, data: GroupChatIn):





