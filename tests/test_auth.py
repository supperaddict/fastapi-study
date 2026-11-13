def register_user(client, username):
    response = client.post(
        "/users",
        json={
            "username": username,
            "age": 25,
            "password": "example123",
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


def login_headers(client, username):
    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": "example123",
        },
    )

    assert response.status_code == 200, response.text
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_login_and_get_me(client):
    user = register_user(client, "auth_user")
    headers = login_headers(client, "auth_user")

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["id"] == user["id"]
    assert response.json()["username"] == "auth_user"


def test_wrong_password_is_rejected(client):
    register_user(client, "wrong_password_user")

    response = client.post(
        "/auth/login",
        json={
            "username": "wrong_password_user",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


def test_cannot_update_another_user(client):
    register_user(client, "user_a")
    other_user = register_user(client, "user_b")
    headers = login_headers(client, "user_a")

    response = client.patch(
        f"/users/{other_user['id']}",
        json={"age": 99},
        headers=headers,
    )

    assert response.status_code == 403, response.text

    response = client.get(f"/users/{other_user['id']}")

    assert response.status_code == 200
    assert response.json()["age"] == 25


def test_change_password(client):
    register_user(client, "password_change_user")
    headers = login_headers(client, "password_change_user")

    # 修改密码
    response = client.post(
        "/auth/change-password",
        json={
            "old_password": "example123",
            "new_password": "new-example456",
        },
        headers=headers,
    )

    assert response.status_code == 204, response.text
    assert response.content == b""

    # 旧密码应失效
    response = client.post(
        "/auth/login",
        json={
            "username": "password_change_user",
            "password": "example123",
        },
    )

    assert response.status_code == 401, response.text

    # 新密码应能登录
    response = client.post(
        "/auth/login",
        json={
            "username": "password_change_user",
            "password": "new-example456",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"
