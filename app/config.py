from dotenv import load_dotenv
import os

# переменные из .env файла загружаются в глобальные переменные os
load_dotenv()

# получение значения из глоб. переменных os 
SECRET_KEY = os.getenv('SECRET_KEY', '1cb3d96ae1eaf6bc3cab5bb775df112ee38419f7773366361ef38ce01a88e3c3')
ALGORITHM=os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))