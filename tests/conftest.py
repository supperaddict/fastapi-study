import os
import secrets
import pytest
import fakeredis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

os.environ.setdefault("JWT_SECRET_KEY", secrets.token_hex(32))
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://unused:unused@127.0.0.1:1/unused")
os.environ["ENABLE_DEMO_ROUTES"] = "true"

from config import settings
from cache import get_cache
from database import get_session
from main import app


@pytest.fixture
def fake_cache():
    cache = fakeredis.FakeRedis(decode_responses=True)
    yield cache
    cache.close()


@pytest.fixture
def client(fake_cache):
    url = settings.test_database_url
    if not url or not make_url(url).database.endswith("_test") or url == settings.database_url:
        raise RuntimeError("测试要求独立的 TEST_DATABASE_URL，库名必须以 _test 结尾")
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()

            def override_session():
                with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                    yield session

            previous = app.dependency_overrides.copy()
            app.dependency_overrides[get_session] = override_session
            app.dependency_overrides[get_cache] = lambda: fake_cache
            try:
                with TestClient(app) as test_client:
                    yield test_client
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(previous)
                transaction.rollback()
    finally:
        engine.dispose()
