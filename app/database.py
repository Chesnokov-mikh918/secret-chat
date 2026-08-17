from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg://bossf2325:wasd1285@localhost:5433/postgres"
engine = create_engine(DATABASE_URL, echo=True)
