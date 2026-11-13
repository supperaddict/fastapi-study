from sqlalchemy import text
from database import engine

with engine.connect() as connection:
    result = connection.execute(
        text("SELECT id, username, age FROM users ORDER BY id")
    )

    for row in result.mappings():
        print(dict(row))