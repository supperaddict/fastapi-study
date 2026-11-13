def test_create_and_read_user(client):
    response = client.post(
        "/users",
        json={
            "username": "pytest_user",
            "age": 25,
            "password": "example123",
            "email": "pytest@example.com",
        },
    )

    assert response.status_code == 201, response.text

    user = response.json()

    assert user["username"] == "pytest_user"
    assert user["age"] == 25
    assert "password" not in user
    assert "hashed_password" not in user

    response = client.get(f"/users/{user['id']}")

    assert response.status_code == 200, response.text
    assert response.json() == user