from fastapi import FastAPI
import uvicorn
from database import engine
from models import Base

app = FastAPI()

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

@app.get("/")
def check():
    return {"Hello": "me"}

if __name__ == "__main__":
    uvicorn.run("main:app")