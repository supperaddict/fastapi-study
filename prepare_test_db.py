from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from config import settings

url = settings.test_database_url
if not url or not make_url(url).database.endswith("_test") or url == settings.database_url:
    raise RuntimeError("TEST_DATABASE_URL 必须指向独立的 *_test 数据库")
config = Config(str(Path(__file__).parent / "alembic.ini"))
config.attributes["database_url"] = url
command.upgrade(config, "head")
print("测试数据库迁移完成")
