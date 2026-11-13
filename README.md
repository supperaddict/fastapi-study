# FastAPI Platform Starter

从 Python 语法练习走到 API 后端项目的一份可运行学习仓库。保留了路由、依赖注入、ORM、JWT、文章权限、缓存和自动化测试的完整链路，方便以后搭建平台时按功能回查。

> 这是学习及平台开发起步项目，不是开箱即用的多租户生产平台。当前用户查询会返回邮箱、文章公开读取；部署真实平台前应按业务收紧可见范围，加入登录限流、组织/角色权限、审计、备份和监控。

## 从哪里读

- [完整学习笔记](docs/学习笔记.md)：从启动命令到请求、数据库、认证、缓存、测试、部署，附排错和独立练习。
- [部署与运维](docs/部署说明.md)：Compose、迁移、HTTPS、日志、备份和升级。
- [验收记录](docs/验收记录.md)：实际执行过的检查及限制。

## 技术栈

Python 3.12+ / FastAPI / Pydantic 2 / SQLAlchemy 2 / PostgreSQL 17 / Alembic / Redis 7 / Argon2 / PyJWT / pytest / HTTPX / Docker Compose / Caddy。

同步数据库和 Redis 使用普通 `def` 接口；异步 HTTP 演示使用 `async def`。用户和文章是通过外键关联的一对多关系。

## 本地运行：继续使用已有的数据库容器

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

把生成结果填入 `.env` 的 `JWT_SECRET_KEY`，并把 `DATABASE_URL`、`TEST_DATABASE_URL` 改成你自己的连接信息。现有学习容器的密码以创建它时的配置为准，不一定等于示例密码。

```bash
alembic upgrade head
python -m uvicorn main:app --reload --port 8001
```

访问 `http://127.0.0.1:8001/docs`。原项目已经有表时，只升级新迁移，不删库、不重跑建表 SQL。旧数据保留；没有密码哈希的历史账号需要设置密码或重新注册。

## 从空环境用 Docker Compose 启动

先按上面步骤准备 `.env` 并替换随机密钥。首次启动前设置 `POSTGRES_PASSWORD` 为自己的随机字母数字密码（若使用特殊字符，连接 URL 中需编码）。

```bash
docker compose up --build -d
docker compose ps
```

Compose 使用自己的命名卷与容器，不映射数据库和 Redis 到宿主机，因此不会抢占你原有 5432/6379 端口。API 使用本机 8001；如旧 Uvicorn 占用该端口，先停止旧服务或修改映射。独立 `migrate` 服务先执行迁移，成功后 API 才启动。

## API 一览

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/health`、`/ready` | 进程存活、数据库就绪 |
| POST | `/users` | 注册，保存密码哈希 |
| GET | `/users`、`/users/{id}` | 用户列表、详情（教学版本公开） |
| PATCH / DELETE | `/users/{id}` | 修改/删除自己的账号 |
| POST | `/auth/login` | JSON 用户名密码登录，获取 JWT |
| GET | `/auth/me` | 当前登录用户 |
| POST | `/auth/change-password` | 校验旧密码并修改，撤销旧 Token |
| POST / GET | `/posts` | 创建文章、分页联表查询 |
| GET / PATCH / DELETE | `/posts/{id}` | 详情缓存、作者修改/删除 |

登录后复制 `access_token`，在 `/docs` 顶部 Authorize 中粘贴，不加 `Bearer `。实际程序通过 `Authorization: Bearer <token>` 传递。

`ENABLE_DEMO_ROUTES=true` 时额外开放 `/tools/summary`、`/tools/http-demo`；默认关闭这些教学接口。

## 测试与代码检查

测试库必须独立、名称以 `_test` 结尾。根据自己的 PostgreSQL 容器名创建一次：

```bash
docker exec fastapi-postgres createdb -U fastapi fastapi_test
python prepare_test_db.py
python -m pytest -q
ruff check .
ruff format --check .
```

测试使用真实 PostgreSQL、事务回滚和内存 FakeRedis；外部 HTTP 用 MockTransport 模拟。不会连接真实 Redis 写缓存。PostgreSQL 序列不随事务回滚，因此编号跳号正常。GitHub Actions 会在空 PostgreSQL 服务上执行迁移、检查和测试。

## 目录

```text
main.py                 应用入口、路由、生命周期、日志、健康检查
config.py               环境配置及随机密钥检查
schemas.py              请求/响应模型
models.py               数据库 ORM 模型
users.py / auth.py      用户、认证接口
posts.py                文章及缓存读取/权限
security.py             密码哈希、Token 签发
cache.py                Redis 连接、缓存失效
数据库入口：database.py  Session 生命周期
依赖：dependencies.py   分页、登录身份、本人权限
migrations/             逐步建表记录
examples/               最初的独立学习脚本
 tests/                  隔离测试配置与回归用例
```

示例脚本执行：`PYTHONPATH=. python examples/check_orm.py`；会访问 `.env` 指定的开发服务。不要在生产数据库中运行练习脚本。

## 当前边界

- 缓存采用 Cache Aside、TTL 和写后失效，提供最终一致性；并发读取回填旧数据及失效失败窗口仍然存在，不能声称强一致。
- Redis 故障会降级读 PostgreSQL；大量缓存同时失效可能增加数据库压力。
- 密码变更使 `auth_version` 递增，旧 Token 被拒绝；登出目前是客户端丢弃 Token，没有单 Token 黑名单或刷新 Token。
- 日志不主动记录请求体、凭证和查询串；不应把 SQL echo 和数据库详细错误打开到公开响应。
- 没有实现前端、微服务、分布式锁或任务队列。后续真实平台应由具体需求决定扩展。
