import logging
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from config import settings
from database import engine
from cache import redis_client
from logging_config import configure_logging
from users import router as users_router
from auth import router as auth_router
from posts import router as posts_router

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    yield
    redis_client.close()
    engine.dispose()


app = FastAPI(title="FastAPI Platform Starter", version="1.0.0", lifespan=lifespan)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(posts_router)
if settings.enable_demo_routes:
    from tools import router as tools_router

    app.include_router(tools_router)


@app.middleware("http")
async def request_log(request, call_next):
    request_id = uuid4().hex
    request.state.request_id = request_id
    start = perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    # 不记录请求体、Token、密码和查询字符串。
    logger.info(
        "request id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (perf_counter() - start) * 1000,
    )
    return response


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    request_id = getattr(request.state, "request_id", uuid4().hex)
    logger.error(
        "unhandled_error request_id=%s", request_id, exc_info=(type(exc), exc, exc.__traceback__)
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "request_id": request_id},
        headers={"X-Request-ID": request_id},
    )


@app.get("/health", tags=["运行状态"])
def health_check():
    return {"status": "ok"}


@app.get("/ready", tags=["运行状态"])
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="数据库尚未就绪")
    # Redis 是可降级缓存，不作为核心就绪条件。
    return {"status": "ready"}
