from pathlib import Path

from alembic import command
from alembic.config import Config


project_dir = Path(__file__).resolve().parent

config = Config(str(project_dir / "alembic.ini"))

config.set_main_option(
    "sqlalchemy.url",
    "postgresql+psycopg://"
    "fastapi:learn123@127.0.0.1:5432/fastapi_test",
)

command.upgrade(config, "head")

print("测试数据库迁移完成")