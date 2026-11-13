import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import get_session
from main import app


test_engine = create_engine(
    "postgresql+psycopg://"
    "fastapi:learn123@127.0.0.1:5432/fastapi_test"
)


@pytest.fixture
def client():
    with test_engine.connect() as connection:
        transaction = connection.begin()

        def override_get_session():
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as session:
                yield session

        previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_session] = override_get_session

        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            transaction.rollback()