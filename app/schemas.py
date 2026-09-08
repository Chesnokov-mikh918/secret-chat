from pydantic import BaseModel, ConfigDict, EmailStr, model_validator, Field

class Base(BaseModel):
    pass

class UserSchemaOut(Base):
    id: int = Field(ge=1)
    username: str = Field(min_length=2, max_length=20)
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class Tokens(Base):
    access_token: str
    refresh_token: str

class UserRegister(Base):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=8, max_length=30) 
    repeat_password: str = Field(min_length=8, max_length=30)
    email: EmailStr

    @model_validator(mode='after')
    def check_passwords(self):
        if self.password != self.repeat_password:
            raise ValueError("Passwords are not the same")
        return self
    
# class MessageSchema(Base):
#     id: int
#     text: str

# try:
#     a = UserRegister(login='asd', password='abc', repeat_password='aec')
#     print(a.login)
# except ValueError as e:
#     print(e) 