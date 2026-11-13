import asyncio
from time import perf_counter


async def fetch_data(name: str):
    print(f"{name}：开始请求")

    # 模拟等待网络响应，不是真的发送 HTTP 请求
    await asyncio.sleep(2)

    print(f"{name}：收到结果")
    return f"{name}的结果"


async def main():
    print("=== 顺序执行 ===")
    start = perf_counter()

    result_a = await fetch_data("A")
    result_b = await fetch_data("B")

    print([result_a, result_b])
    print(f"耗时：{perf_counter() - start:.2f} 秒")

    print("\n=== 并发执行 ===")
    start = perf_counter()

    results = await asyncio.gather(
        fetch_data("A"),
        fetch_data("B"),
    )

    print(results)
    print(f"耗时：{perf_counter() - start:.2f} 秒")


asyncio.run(main())
