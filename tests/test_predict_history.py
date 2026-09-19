def _signup_and_login(client, email):
    client.post("/auth/signup", json={"email": email, "password": "testpass123"})
    login_res = client.post("/auth/login", json={"email": email, "password": "testpass123"})
    return login_res.json()["access_token"]


def test_predict_requires_auth(client):
    response = client.post("/predict", json={"complaint_text": "This is a real complaint text here."})
    assert response.status_code == 401  # no Authorization header at all


def test_predict_rejects_short_text(client):
    token = _signup_and_login(client, "shorttext@example.com")
    response = client.post(
        "/predict",
        json={"complaint_text": "hi"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422  # min_length=10 validation


def test_predict_returns_expected_shape(client):
    token = _signup_and_login(client, "shapecheck@example.com")
    response = client.post(
        "/predict",
        json={"complaint_text": "I was charged an unauthorized fee and have proof of payment."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for field in ["predicted_label", "probability_of_relief", "meaning",
                  "explanation", "tip", "top_words_toward_relief", "top_words_toward_no_relief"]:
        assert field in data


def test_history_isolated_between_users(client):
    """The exact security property manually verified in Step 10, now automated."""
    token_a = _signup_and_login(client, "usera@example.com")
    token_b = _signup_and_login(client, "userb@example.com")

    client.post(
        "/predict",
        json={"complaint_text": "User A's complaint about a late fee dispute."},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    history_b = client.get("/history", headers={"Authorization": f"Bearer {token_b}"})
    assert history_b.status_code == 200
    assert history_b.json() == []  # User B must see nothing from User A