import jwt
from pwdlib import PasswordHash
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, or_
from models import UserBase
from schemas import UserSchemaOut, Tokens, UserRegister
import uuid


auth_router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_async_db)]
LoginData = Annotated[OAuth2PasswordRequestForm, Depends()]

# выбор настройки хэширования
password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_hash_for_password(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(data: dict) -> str:
    """Создание access токена"""
    if 'exp' not in data:
        # отсчет к просрочке начиная с текущего момента мирового времени
        data['exp'] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode(data, SECRET_KEY, ALGORITHM)
    return access_token

def create_refresh_token() -> str:
    """Создание refresh токена"""
    refresh_token = str(uuid.uuid4())
    return refresh_token

# надо проверить эту функцию еще
async def authenticate_user(login: str, password: str, db: DbSession):
    query = select(UserBase).where(UserBase.username == login)
    res = (await db.execute(query)).scalars().first()
    if not res:
        verify_password("long_waiting_create", get_hash_for_password("another_waiting"))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не существует такого пользователя") 
    if verify_password(password, res.hashed_password):
        return UserSchemaOut(id=res.id, username=res.username, email=res.email)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не существует такого пользователя")

@auth_router.post("/login")
async def login_for_access_token(data: LoginData, db: DbSession):
    # если Depends пустой(без параметров), то прога думает, что надо создать объект класса, рядом с которым и находится Depends
    user = await authenticate_user(data.username, data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не существует такого пользователя")
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token() # надо его сохранять в бд еще
    return Tokens(access_token=access_token, refresh_token=refresh_token)
    # В гите еще разобраться что делают кнопки индексировать изменения и делают ли они коммит таким образзом или нет

@auth_router.post("/register")
async def register_user(user: UserRegister, db: DbSession):
    query = select(UserBase).where(
        or_(
            UserBase.email == user.email, 
            UserBase.username == user.username
        )
    )

    res = (await db.execute(query)).scalar()

    if res:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail = "Пользователь с таким логином или почтой уже существует"
        )

    new_user = UserBase(
        username = user.username,
        email = user.email, 
        hashed_password = get_hash_for_password(user.password)
    )
    db.add(new_user)
    await db.commit()
    # после коммита все данные SQLAlchemy считает неактуальными, потому надо их обновить 
    await db.refresh(new_user) 
    return new_user
    
    # сделать тесты для проверки авторизации в отдельном файле, и отдельно race condition
    # почитать про транзакции и изоляции в postgresql
    # надо сделать привязку refresh токена в бд к пользователю