"""集中读取配置；应用、迁移、脚本共用。"""

from functools import lru_cache
from pathlib import Path
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).parent / ".env", extra="ignore")
    database_url: str
    test_database_url: str | None = None
    redis_url: str = "redis://127.0.0.1:6379/0"
    jwt_secret_key: SecretStr
    token_minutes: int = Field(default=30, ge=1, le=1440)
    cache_ttl: int = Field(default=60, ge=1)
    log_level: str = "INFO"
    enable_demo_routes: bool = False

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret(cls, value):
        if len(value.get_secret_value()) < 32 or value.get_secret_value().startswith("CHANGE_ME"):
            raise ValueError("JWT_SECRET_KEY 必须为至少32字符的随机密钥")
        return value


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
