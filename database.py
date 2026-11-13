from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DATABASE_URL = (
    "postgresql+psycopg://"
    "fastapi:learn123@127.0.0.1:5432/fastapi_study"
)

def get_connection():
    with engine.connect() as connection:
        yield connection


engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session