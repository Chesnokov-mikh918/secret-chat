from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import asyncio

DATABASE_URL = "postgresql+asyncpg://bossf2325:wasd1285@localhost:5433/postgres"
engine = create_async_engine(DATABASE_URL, echo=True)
# async_sessionmaker это фабрика классов(создает экзмепляры, тут мы создаем фабрику)
AsyncSessionLocal = async_sessionmaker(bind=engine)

async def get_async_db():
    # при каждом открыти контекстного менеджера создается объект типа AsyncSession
    async with AsyncSessionLocal() as session:
        yield session
    