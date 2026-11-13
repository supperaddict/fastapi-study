from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Identity,
    String,
    Text,
)

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("age BETWEEN 0 AND 150"),
    )

    id: Mapped[int] = mapped_column(
        Identity(always=True),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(
        String(20),
        unique=True,
    )
    age: Mapped[int]
    email: Mapped[str | None] = mapped_column(String(255))

    hashed_password: Mapped[str | None] = mapped_column(String(255))

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(
        Identity(always=True),
        primary_key=True,
    )
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )