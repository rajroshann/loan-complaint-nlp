def test_signup_success(client):
    response = client.post("/auth/signup", json={
        "email": "newuser@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "password" not in data  # UserResponse must never leak the hash


def test_signup_duplicate_email_rejected(client):
    client.post("/auth/signup", json={"email": "dup@example.com", "password": "testpass123"})
    response = client.post("/auth/signup", json={"email": "dup@example.com", "password": "anotherpass"})
    assert response.status_code == 400


def test_login_success(client):
    client.post("/auth/signup", json={"email": "loginuser@example.com", "password": "testpass123"})
    response = client.post("/auth/login", json={"email": "loginuser@example.com", "password": "testpass123"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_rejected(client):
    client.post("/auth/signup", json={"email": "wrongpass@example.com", "password": "testpass123"})
    response = client.post("/auth/login", json={"email": "wrongpass@example.com", "password": "incorrect"})
    assert response.status_code == 401