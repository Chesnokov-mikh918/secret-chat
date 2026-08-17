from pydantic import BaseModel

class Base(BaseModel):
    pass

class UserSchema(Base):
    id: int
    name: str

class MessageSchema(Base):
    id: int
    text: str

