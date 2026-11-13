from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=20)
    age: int = Field(ge=0, le=150)
    password: str = Field(min_length=8)
    email: EmailStr | None = Field(default=None, max_length=255)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    age: int
    email: str | None


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None, min_length=1, max_length=20
    )
    age: int | None = Field(default=None, ge=0, le=150)
    email: EmailStr | None = Field(default=None, max_length=255)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)

class PostCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=10000)


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    author_id: int

class PostListItem(BaseModel):
    id: int
    title: str
    author_id: int
    author_username: str

class PostListItem(BaseModel):
    id: int
    title: str
    author_id: int
    author_username: str

class PostUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    content: str | None = Field(
        default=None, min_length=1, max_length=10000
    )