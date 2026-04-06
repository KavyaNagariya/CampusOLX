import pytest


@pytest.mark.asyncio
async def test_create_and_list_items(client, seed_categories):
    # Signup & login
    await client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Seller",
            "email": "seller@example.com",
            "phone": "8888888888",
            "password": "password123",
        },
    )

    login = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "seller@example.com",
            "password": "password123",
        },
    )

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    item_data = {
        "title": "Physics Book",
        "description": "Used physics textbook",
        "price": 300,
        "pickup_location": "Hostel A",
        "available_till": "2030-01-01T00:00:00",
        "category_id": 1,
    }

    # Create item
    response = await client.post(
        "/api/v1/items/",
        json=item_data,
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Physics Book"

    # List items
    response = await client.get("/api/v1/items/")
    assert response.status_code == 200
    assert len(response.json()) >= 1
