import asyncio
import httpx
from fastapi import HTTPException
from time import perf_counter

from fastapi import APIRouter

router = APIRouter(prefix="/tools", tags=["异步练习"])


async def fetch_data(name: str):
    await asyncio.sleep(2)
    return {"name": name, "result": "完成"}


@router.get("/summary")
async def get_summary():
    start = perf_counter()

    results = await asyncio.gather(
        fetch_data("A"),
        fetch_data("B"),
    )

    return {
        "results": results,
        "elapsed_seconds": round(perf_counter() - start, 2),
    }

@router.get("/http-demo")
async def http_demo(keyword: str = "python"):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://httpbin.org/get",
                params={"keyword": keyword},
            )

            response.raise_for_status()

            data = response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="外部服务响应超时",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="无法连接外部服务",
        )
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="外部服务返回异常状态",
        )
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="外部服务未返回合法 JSON",
        )

    return {
        "message": "外部请求成功",
        "upstream_data": data,
    }