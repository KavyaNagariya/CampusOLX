import pytest


@pytest.mark.asyncio
async def test_reservation_flow(client):
    # Seller
    await client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Seller",
            "email": "seller2@example.com",
            "phone": "7777777777",
            "password": "password123",
        },
    )

    seller_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "seller2@example.com",
            "password": "password123",
        },
    )
    seller_token = seller_login.json()["access_token"]

    # Buyer
    await client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Buyer",
            "email": "buyer@example.com",
            "phone": "6666666666",
            "password": "password123",
        },
    )

    buyer_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "buyer@example.com",
            "password": "password123",
        },
    )
    buyer_token = buyer_login.json()["access_token"]

    # Seller posts item
    item = await client.post(
        "/api/v1/items/",
        json={
            "title": "Calculator",
            "description": "Scientific calculator",
            "price": 500,
            "pickup_location": "Library",
            "available_till": "2030-01-01T00:00:00",
            "category_id": 1,
        },
        headers={"Authorization": f"Bearer {seller_token}"},
    )

    item_id = item.json()["id"]

    # Buyer requests reservation
    reservation = await client.post(
        "/api/v1/reservations/",
        json={"item_id": item_id},
        headers={"Authorization": f"Bearer {buyer_token}"},
    )
    assert reservation.status_code == 200

    reservation_id = reservation.json()["id"]

    # Seller accepts reservation
    response = await client.post(
        f"/api/v1/reservations/{reservation_id}/accept",
        headers={"Authorization": f"Bearer {seller_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

