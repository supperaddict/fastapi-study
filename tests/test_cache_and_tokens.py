import jwt
from redis.exceptions import ConnectionError
from security import SECRET_KEY, ALGORITHM


def account(client, name="cache_owner"):
    created = client.post("/users", json={"username": name, "age": 20, "password": "example123"})
    assert created.status_code == 201, created.text
    logged = client.post("/auth/login", json={"username": name, "password": "example123"})
    assert logged.status_code == 200
    return created.json(), {"Authorization": "Bearer " + logged.json()["access_token"]}


def article(client, headers):
    response = client.post("/posts", headers=headers, json={"title": "缓存测试", "content": "正文"})
    assert response.status_code == 201, response.text
    return response.json()


def test_cache_hit_update_delete(client, fake_cache, monkeypatch):
    _, headers = account(client)
    post = article(client, headers)
    path = f"/posts/{post['id']}"
    key = f"posts:detail:{post['id']}"
    assert client.get(path).status_code == 200
    assert fake_cache.exists(key)
    assert 0 < fake_cache.ttl(key) <= 60
    # 命中时不应再按主键读取文章。
    from sqlalchemy.orm import Session

    original = Session.get

    def forbid_get(*args, **kwargs):
        raise AssertionError("缓存命中仍访问了数据库")

    with monkeypatch.context() as patch:
        patch.setattr(Session, "get", forbid_get)
        assert client.get(path).json()["title"] == "缓存测试"
    assert Session.get == original
    assert client.patch(path, headers=headers, json={"title": "新标题"}).status_code == 200
    assert not fake_cache.exists(key)
    assert client.get(path).json()["title"] == "新标题"
    assert client.delete(path, headers=headers).status_code == 204
    assert client.get(path).status_code == 404


def test_deleted_account_invalidates_articles(client, fake_cache):
    user, headers = account(client)
    post = article(client, headers)
    path = f"/posts/{post['id']}"
    assert client.get(path).status_code == 200
    assert client.delete(f"/users/{user['id']}", headers=headers).status_code == 204
    assert not fake_cache.exists(f"posts:detail:{post['id']}")
    assert client.get(path).status_code == 404


def test_password_change_revokes_old_token(client):
    _, headers = account(client)
    response = client.post(
        "/auth/change-password",
        headers=headers,
        json={"old_password": "example123", "new_password": "changed-password"},
    )
    assert response.status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401
    result = client.post(
        "/auth/login", json={"username": "cache_owner", "password": "changed-password"}
    )
    assert result.status_code == 200
    assert (
        client.get(
            "/auth/me", headers={"Authorization": "Bearer " + result.json()["access_token"]}
        ).status_code
        == 200
    )


def test_redis_unavailable_falls_back(client, fake_cache, monkeypatch):
    _, headers = account(client)
    post = article(client, headers)

    def unavailable(*args, **kwargs):
        raise ConnectionError("模拟 Redis 断线")

    monkeypatch.setattr(fake_cache, "get", unavailable)
    monkeypatch.setattr(fake_cache, "set", unavailable)
    response = client.get(f"/posts/{post['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "缓存测试"


def test_invalid_and_expired_tokens(client):
    _, headers = account(client)
    token = headers["Authorization"].split()[1]
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    payload["exp"] = 1
    expired = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    assert client.get("/auth/me", headers={"Authorization": "Bearer " + expired}).status_code == 401
    assert (
        client.get("/auth/me", headers={"Authorization": "Bearer broken-token"}).status_code == 401
    )
