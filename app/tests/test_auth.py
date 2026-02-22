import pytest


@pytest.mark.asyncio
async def test_signup_and_login(client):
    signup_data = {
        "name": "Test User",
        "email": "testuser@example.com",
        "phone": "9999999999",
        "password": "password123",
    }

    # Signup
    response = await client.post("/api/v1/auth/signup", json=signup_data)
    assert response.status_code == 200
    assert response.json()["email"] == signup_data["email"]

    # Login
    login_data = {
        "email": signup_data["email"],
        "password": signup_data["password"],
    }

    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()

