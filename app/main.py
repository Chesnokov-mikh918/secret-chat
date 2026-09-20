from fastapi import FastAPI
import uvicorn
from database import engine
from auth.models import Base
from auth.auth import auth_router
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

# lifespan это по сути функция, которая делает что то до того как сервер начнет принимать запросы
# и что то после этого(это реализовано через yield и async конт. менеджеры)
# asynccontextmanager нужен тк сам сервер реализует функцию инициализации через него 
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)