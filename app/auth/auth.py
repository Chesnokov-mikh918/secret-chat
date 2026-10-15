import jwt
from pwdlib import PasswordHash
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from database import DbSession
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, or_, update
from auth.models import UserModel
from auth.schemas import UserSchemaOut, Token, UserRegister
import uuid
import hashlib

auth_router = APIRouter()

LoginData = Annotated[OAuth2PasswordRequestForm, Depends()]

def get_hash_for_refresh(refr_tok: str) -> str:
    return hashlib.sha256(refr_tok.encode()).hexdigest()

# выбор настройки хэширования
password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_hash_for_password(password: str) -> str:
    return password_hash.hash(password)

def set_tokens_in_cookie(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key = 'access_token', 
        value = access_token,
        httponly = True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,
        samesite="lax",
    )

    response.set_cookie(
        key='refresh_token',
        value = refresh_token,
        httponly = True,
        secure=False,
        samesite="lax",
    )

def get_access_from_cookie(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token not found'
        )
    return token

def create_access_token(data: dict) -> str:
    """Создание access токена"""
    if 'exp' not in data:
        # отсчет к просрочке начиная с текущего момента мирового времени
        data['exp'] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data['jti'] = str(uuid.uuid4())
    access_token = jwt.encode(data, SECRET_KEY, ALGORITHM)
    return access_token

def create_refresh_token() -> str:
    """Создание refresh токена"""
    refresh_token = str(uuid.uuid4())
    return refresh_token

async def authenticate_user(login: str, password: str, db: DbSession):
    query = select(UserModel).where(
        or_(
            UserModel.username == login, 
            UserModel.email == login
        )
    )
    res = (await db.execute(query)).scalars().first()
    if not res:
        verify_password("long_waiting_create", get_hash_for_password("another_waiting"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Не существует такого пользователя"
        ) 
    if verify_password(password, res.hashed_password):
        return UserSchemaOut(
            id=res.id, 
            username=res.username, 
            email=res.email
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Не существует такого пользователя"
    )

@auth_router.post("/login")
async def login_for_access_token(response: Response, data: LoginData, db: DbSession):
    # если Depends пустой(без параметров), то прога думает, что надо создать объект класса, рядом с которым и находится Depends
    user = await authenticate_user(data.username, data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Не существует такого пользователя"
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token()

    hashed_refresh_token = get_hash_for_refresh(refresh_token)

    query = update(UserModel).where(UserModel.id == user.id).values(refresh_token=hashed_refresh_token)
    await db.execute(query)
    await db.commit()

    set_tokens_in_cookie(
        response=response, 
        access_token=access_token,
        refresh_token=refresh_token
    )

    return Token(token=access_token, token_type = "access_token")
    # В гите еще разобраться что делают кнопки индексировать изменения и делают ли они коммит таким образзом или нет

@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister, db: DbSession):
    query = select(UserModel).where(
        or_(
            UserModel.email == user.email, 
            UserModel.username == user.username
        )
    )

    res = (await db.execute(query)).scalar()

    if res:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail = "Пользователь с таким логином или почтой уже существует"
        )

    new_user = UserModel(
        username = user.username,
        email = user.email, 
        hashed_password = get_hash_for_password(user.password)
    )
    db.add(new_user)
    await db.commit()
    # после коммита все данные SQLAlchemy считает неактуальными, потому надо их обновить 
    await db.refresh(new_user) 
    return new_user

# эта функция нужна для того чтобы при любом действии на сайте узнавать кто его делает
async def get_current_user(db: DbSession, token: str = Depends(get_access_from_cookie)): 
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid"
        )

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid(no sub in payload)"
        )

    query = select(UserModel).where(UserModel.id == int(user_id))
    user = (await db.execute(query)).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid(no user with such id)"
        )
    
    return user 

@auth_router.post("/refresh")
async def get_access_token_from_refresh(request: Request, response: Response, db: DbSession):
    refr_token = request.cookies.get('refresh_token')
    if not refr_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tokens are invalid or dont exist"
        )

    hashed_refr = get_hash_for_refresh(refr_token)
    query = select(UserModel).where(UserModel.refresh_token == hashed_refr)
    user = (await db.execute(query)).scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tokens are invalid or dont exist"
        )
    
    access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token()
    user.refresh_token = get_hash_for_refresh(new_refresh_token)

    set_tokens_in_cookie(
        response=response, 
        access_token=access_token,
        refresh_token=new_refresh_token
    )
    
    await db.commit()
    return Token(token=access_token, token_type="access_token")

@auth_router.post("/logout")
async def logout(response: Response, db: DbSession, user = Depends(get_current_user)):
    query = update(UserModel).where(UserModel.id == user.id).values(refresh_token="")
    await db.execute(query)
    await db.commit()
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return {"ok": "ok"}
    # Tasks to do:
    # разобраться с токенами в куках, почему рефреш токен пропадает и появляется
    # сделать логирование через middlewares
    # почитать про публичный и секретный ключ и как делается проверка
    # почему нельзя хранить access токен в локалсторэдж и попытаться его стырить
    # сделать тесты для проверки авторизации в отдельном файле, и отдельно race condition
    # почитать про транзакции и изоляции в postgresql
    
    # идеи на дальнейшее развитие авторизации:
    # сделать кнопку забыл пароль
    # сделать подтверждение почты по письму
    # сделать ограничение на попытки залогиниться с одного айпи
    # убрать почту с authorization_user ручки
    # проверить можно ли оставить такие же http-запросы