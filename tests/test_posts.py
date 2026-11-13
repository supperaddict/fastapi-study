def create_account(client, username):
    response = client.post(
        "/users",
        json={
            "username": username,
            "age": 25,
            "password": "example123",
        },
    )
    assert response.status_code == 201, response.text
    user = response.json()

    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": "example123",
        },
    )
    assert response.status_code == 200, response.text

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return user, headers


def create_article(client, headers):
    response = client.post(
        "/posts",
        json={
            "title": "测试文章",
            "content": "原始正文",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_author_can_update_and_delete_post(client):
    author, headers = create_account(client, "post_author")
    post = create_article(client, headers)

    assert post["author_id"] == author["id"]

    response = client.patch(
        f"/posts/{post['id']}",
        json={"title": "新标题"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["title"] == "新标题"
    assert response.json()["content"] == "原始正文"

    response = client.get(f"/posts/{post['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "新标题"

    response = client.delete(
        f"/posts/{post['id']}",
        headers=headers,
    )
    assert response.status_code == 204, response.text

    response = client.get(f"/posts/{post['id']}")
    assert response.status_code == 404


def test_other_user_cannot_modify_post(client):
    _, author_headers = create_account(client, "owner")
    _, other_headers = create_account(client, "other_user")
    post = create_article(client, author_headers)

    response = client.patch(
        f"/posts/{post['id']}",
        json={"title": "不应该成功的修改"},
        headers=other_headers,
    )
    assert response.status_code == 403, response.text

    response = client.delete(
        f"/posts/{post['id']}",
        headers=other_headers,
    )
    assert response.status_code == 403, response.text

    response = client.get(f"/posts/{post['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "测试文章"
    assert response.json()["author_id"] == post["author_id"]
