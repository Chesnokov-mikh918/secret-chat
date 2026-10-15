from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

DATABASE_URL = "postgresql+asyncpg://bossf2325:wasd1285@localhost:5433/postgres"
engine = create_async_engine(DATABASE_URL, echo=False)
# async_sessionmaker это фабрика классов(создает экзмепляры, тут мы создаем фабрику)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_async_db():
    # при каждом открыти контекстного менеджера создается объект типа AsyncSession
    async with AsyncSessionLocal() as session:
        yield session

DbSession = Annotated[AsyncSession, Depends(get_async_db)]