from sqlalchemy import select
from sqlalchemy.orm import Session

from database import engine
from models import User


with Session(engine) as session:
    statement = select(User).order_by(User.id)

    users = session.scalars(statement).all()

    for user in users:
        print(user.id, user.username, user.age)