# CampusOLX Marketplace Backend

FastAPI backend for a campus buy/sell marketplace with JWT auth, item listings, reservation flow, moderation, reports, ratings, and image upload support.

## Project Scope

This repository currently contains backend code under `backend/`.

## Tech Stack

- Python 3.12+
- FastAPI
- SQLAlchemy (async)
- Alembic
- PostgreSQL (via asyncpg)
- JWT (`python-jose`)
- Password hashing (`passlib[bcrypt]`)
- Pytest + HTTPX
- Cloudinary (image uploads)

## Directory Layout

```text
backend/
  app/
    api/v1/           # Route handlers
    core/             # Config, security, permissions, constants
    db/               # Engine/session/base/init
    models/           # SQLAlchemy models
    schemas/          # Pydantic request/response models
    services/         # Business logic
    tests/            # Async API tests
    utils/            # Helpers (pagination, validators, image upload)
  alembic/            # DB migrations
  requirements.txt
  alembic.ini
```

## Environment Variables

Create `backend/.env` with:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
DATABASE_URL_POOLER=postgresql+asyncpg://user:password@host:5432/dbname
DEBUG=True
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

Notes:
- `DATABASE_URL` is used by Alembic migration config.
- `DATABASE_URL_POOLER` is used by the async app engine in `app/db/session.py`.

## Local Setup

From repository root:

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- Base URL: `http://127.0.0.1:8000`
- OpenAPI docs: `http://127.0.0.1:8000/docs`
- Health endpoint: `GET /`

## Database and Migrations

Run migrations:

```bash
cd backend
alembic upgrade head
```

Create a migration:

```bash
cd backend
alembic revision --autogenerate -m "your_message"
```

## API Surface (v1)

All routes are prefixed with `/api/v1`.

- Auth
- `POST /auth/signup`
- `POST /auth/login`

- Users
- `GET /users/me`

- Items
- `POST /items/`
- `GET /items/`
- `POST /items/{item_id}/image`
- `GET /items/me` - Get my listings
- `GET /items/purchases` - Get my purchases
- `DELETE /items/{item_id}` - Delete own item (seller or admin)

- Categories
- `GET /categories/`

- Reservations
- `POST /reservations/` - Create reservation request
- `GET /reservations/` - List user's reservations (as buyer/seller)
- `GET /reservations/{reservation_id}` - Get specific reservation
- `POST /reservations/{reservation_id}/accept` - Seller accepts
- `POST /reservations/{reservation_id}/reject` - Seller rejects
- `POST /reservations/{reservation_id}/cancel` - Buyer/seller cancels
- `POST /reservations/{reservation_id}/sold` - Seller confirms sale

- Reports
- `POST /reports/`

- Ratings
- `POST /ratings/`

- Admin
- `POST /admin/block-user/{user_id}`
- `DELETE /admin/soft-delete-item/{item_id}`
- `DELETE /admin/hard-delete-item/{item_id}`

## Documentation

> **Important:** After making any changes to the codebase, please update the `ARCHITECTURE.md` file to reflect the new architecture, endpoints, or logic. This ensures the documentation stays in sync with the implementation.

## Tests

```bash
cd backend
pytest -q
```

Current tests cover:
- signup/login
- create/list items
- reservation request/accept flow

## Current Codebase Notes

Based on current implementation:
- Startup runs `init_db()` which creates tables and seeds default categories when empty.
- Reservation flow uses row locking (`FOR UPDATE`) and item timeout logic (`Item.is_actually_available`).
- Item image upload route exists and persists `image_url`.

## Development Notes

- Keep `.env` in `backend/.env`.
- Do not commit local DB files, caches, or virtual environments.
- Keep model/schema/service changes aligned before generating migrations.
