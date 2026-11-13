import json

from cache import redis_client


try:
    print("连接测试：", redis_client.ping())

    post = {
        "id": 123,
        "title": "学习 Redis",
        "content": "这是缓存练习。",
        "author_id": 1,
    }

    key = "learning:post:123"

    # 字典转成 JSON 字符串，保存 60 秒
    redis_client.set(
        key,
        json.dumps(post, ensure_ascii=False),
        ex=60,
    )

    cached = redis_client.get(key)

    if cached is not None:
        restored_post = json.loads(cached)

        print("读取结果：", restored_post)
        print("标题：", restored_post["title"])
        print("剩余秒数：", redis_client.ttl(key))

finally:
    redis_client.close()
