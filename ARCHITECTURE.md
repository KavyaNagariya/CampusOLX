# Architecture

**Analysis Date:** 2026-02-27
**Last Updated:** 2026-02-27

## Pattern Overview

**Overall:** Layered Architecture with Service-Oriented Business Logic

This is a **FastAPI-based REST API** backend following a **layered architecture pattern** with clear separation between:
- **API Layer** (route handlers)
- **Service Layer** (business logic)
- **Data Layer** (models and database)

The application uses **async/await** throughout for non-blocking I/O operations, particularly for database access via SQLAlchemy's async driver.

## Layers

### API Layer (`app/api/`)

**Purpose:** Handle HTTP requests and responses, apply authentication, delegate to services

**Location:** `app/api/v1/`

**Contains:**
- Route handlers (FastAPI routers)
- Dependency injection (`app/api/deps.py`)
- Request validation through Pydantic schemas

**Key Files:**
- `app/api/v1/router.py` - Main router aggregating all endpoints
- `app/api/deps.py` - Dependency injection (OAuth2 scheme, get_current_user)

**Endpoints Structure:**
```
/api/v1/
├── /auth/          # Authentication (signup, login)
├── /users/         # User profile
├── /items/         # Item CRUD, images, my listings, my purchases, delete own item
├── /categories/    # Item categories
├── /reservations/  # Reservation workflow (CRUD + accept/reject/cancel/sold)
├── /reports/       # Item/user reports
├── /ratings/       # User ratings
└── /admin/         # Admin operations (block user, soft/hard delete)
```

---

### Service Layer (`app/services/`)

**Purpose:** Encapsulate business logic, orchestrate data operations, enforce business rules

**Location:** `app/services/`

**Contains:**
- `auth_service.py` - User registration and authentication
- `item_service.py` - Item CRUD, search, listing management
- `reservation_service.py` - Complete reservation workflow with row locking
- `admin_service.py` - User blocking, item soft removal
- `report_service.py` - Report creation

**Pattern:**
```python
async def service_function(db: AsyncSession, ...) -> DomainModel:
    # 1. Fetch data
    # 2. Validate business rules
    # 3. Modify state
    # 4. Commit
    # 5. Return domain model
```

---

### Data Layer

#### Models (`app/models/`)

**Purpose:** SQLAlchemy ORM definitions mapping to PostgreSQL tables

**Files:**
- `user.py` - User entity with roles and relationships
- `item.py` - Item listing with status, reservation tracking
- `category.py` - Item categories
- `reservation.py` - Reservation requests between buyers and sellers
- `report.py` - User reports for moderation
- `rating.py` - User-to-user ratings

**Key Relationships:**
```python
# User -> Items (one-to-many)
User.items_for_sale = relationship("Item", foreign_keys=[Item.seller_id])

# User -> Reserved Items (one-to-many)
User.reserved_items = relationship("Item", foreign_keys=[Item.reserved_by_id])

# Category -> Items (one-to-many)
Category.items = relationship("Item")

# Item -> Reservations (one-to-many, cascade delete)
Item.reservations = relationship("Reservation", cascade="all, delete-orphan")
```

#### Database Session (`app/db/`)

**Location:** `app/db/`

**Files:**
- `session.py` - Async SQLAlchemy engine and session factory
- `base.py` - DeclarativeBase for models
- `init_db.py` - Table creation and category seeding

---

### Schemas Layer (`app/schemas/`)

**Purpose:** Pydantic models for request validation and response serialization

**Files:**
- `user.py` - UserCreate, UserResponse
- `item.py` - ItemCreate, ItemResponse
- `auth.py` - LoginRequest, TokenResponse
- `reservation.py` - ReservationCreate, ReservationResponse
- `report.py` - ReportCreate, ReportResponse
- `category.py` - CategoryResponse
- `rating.py` - RatingCreate, RatingResponse

---

### Core/Configuration Layer (`app/core/`)

**Purpose:** Cross-cutting concerns, security, constants

**Files:**
- `config.py` - Settings via pydantic-settings, loads from `.env`
- `security.py` - Password hashing (bcrypt), JWT token creation/verification
- `constants.py` - Enums for UserRole, ItemStatus, ReservationStatus, ReportReason
- `permissions.py` - Dependency functions require_user, require_admin

---

### Utilities (`app/utils/`)

**Purpose:** Shared helper functions

**Files:**
- `image_upload.py` - Cloudinary integration for item images
- `pagination.py` - Pagination helpers (if used)
- `validators.py` - Custom validation logic

---

## Data Flow

### Authentication Flow:

1. **Signup:** `POST /api/v1/auth/signup`
   - API receives `UserCreate` schema
   - `auth_service.register_user()` hashes password, creates User record
   - Returns `UserResponse`

2. **Login:** `POST /api/v1/auth/login`
   - OAuth2PasswordRequestForm (username=email, password)
   - `auth_service.authenticate_user()` verifies credentials
   - `security.create_access_token()` generates JWT
   - Returns `TokenResponse` with access_token

### Item Listing Flow:

1. **Create Item:** `POST /api/v1/items/`
   - Requires JWT (get_current_user dependency)
   - `item_service.create_item()` creates Item record
   - Handles timezone-aware datetime conversion
   - Returns `ItemResponse`

2. **Browse Items:** `GET /api/v1/items/`
   - Optional query params: q (search), category_id, max_price, limit, offset
   - `item_service.list_available_items()` queries with filters
   - Returns list of `ItemResponse`

3. **My Listings:** `GET /api/v1/items/me`
   - Returns all items posted by current user

4. **My Purchases:** `GET /api/v1/items/purchases`
   - Returns all items reserved by current user

5. **Delete Own Item:** `DELETE /api/v1/items/{item_id}`
   - Requires JWT
   - Only the item seller or admin can delete
   - Hard deletes the item from database

### Reservation Flow (Complete):

1. **Request Reservation:** `POST /api/v1/reservations/`
   - Requires JWT
   - `reservation_service.request_reservation()`:
     - Locks item row (`SELECT ... FOR UPDATE`)
     - Validates 5-minute timeout (`Item.is_actually_available`)
     - Prevents self-reservation
     - Creates Reservation record (status=REQUESTED)
     - Updates Item to RESERVED
   - Returns `ReservationResponse`

2. **Accept Reservation:** `POST /api/v1/reservations/{reservation_id}/accept`
   - Requires JWT, must be item seller
   - `reservation_service.accept_reservation()`:
     - Locks reservation row
     - Validates ownership and status
     - Updates status to ACCEPTED

3. **Reject Reservation:** `POST /api/v1/reservations/{reservation_id}/reject`
   - Requires JWT, must be item seller
   - `reservation_service.reject_reservation()`:
     - Sets reservation status to REJECTED
     - Releases item back to AVAILABLE

4. **Cancel Reservation:** `POST /api/v1/reservations/{reservation_id}/cancel`
   - Requires JWT, buyer or seller can cancel
   - `reservation_service.cancel_reservation()`:
     - Sets reservation status to CANCELLED
     - Releases item back to AVAILABLE

5. **Confirm Sale:** `POST /api/v1/reservations/{reservation_id}/sold`
   - Requires JWT, must be item seller
   - `reservation_service.confirm_sale()`:
     - Sets reservation status to ACCEPTED
     - Marks item as SOLD

6. **Get Reservations:** `GET /api/v1/reservations/`
   - Returns all reservations where user is buyer or seller

---

## Key Abstractions

### Authentication/Authorization

**OAuth2PasswordBearer** in `app/api/deps.py`:
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    # JWT decode -> extract user_id -> fetch User
    # Checks: valid token, user exists, user not blocked
```

**Permission Dependencies** in `app/core/permissions.py`:
```python
def require_user(current_user: User = Depends(get_current_user)) -> User:
    # Blocked users cannot access protected endpoints

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    # Only UserRole.ADMIN can access
```

### Reservation Timeout

**Smart Availability** in `app/models/item.py`:
```python
@property
def is_actually_available(self) -> bool:
    """If item is RESERVED but 5+ minutes old, treat as AVAILABLE"""
    if self.status == ItemStatus.AVAILABLE:
        return True
    if self.status == ItemStatus.RESERVED and self.reserved_at:
        five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
        return self.reserved_at < five_mins_ago
    return False
```

### Item Deletion

**Three ways to delete an item:**

1. **Owner Delete:** `DELETE /api/v1/items/{item_id}`
   - Item seller can delete their own item
   - Admin can also delete any item
   - Hard delete from database

2. **Admin Soft Delete:** `DELETE /api/v1/admin/soft-delete-item/{item_id}`
   - Only admin can use
   - Sets item status to SOLD (item remains in DB)

3. **Admin Hard Delete:** `DELETE /api/v1/admin/hard-delete-item/{item_id}`
   - Only admin can use
   - Removes item entirely from database

### Row Locking for Concurrency

**In `app/services/reservation_service.py`:**
```python
# Prevent race conditions on concurrent reservation requests
stmt = select(Item).where(Item.id == item_id).with_for_update()
result = await db.execute(stmt)
item = result.scalar_one_or_none()
```

### DateTime Handling

**Timezone-aware to timezone-naive conversion** in `app/services/item_service.py`:
```python
item_data = item_in.model_dump()
if item_data.get("available_till") and item_data["available_till"].tzinfo:
    item_data["available_till"] = item_data["available_till"].replace(tzinfo=None)
```

---

## Entry Points

### Main Application

**Location:** `app/main.py`

```python
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=..., allow_credentials=True, ...)

# API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check
@app.get("/")
async def root():
    return {"message": "Campus Marketplace API is running"}
```

**Run Command:**
```bash
uvicorn app.main:app --reload --port 8000
```

---

## Error Handling

**Pattern:** HTTPException with status codes

```python
# Not found
raise HTTPException(status_code=404, detail="Item not found")

# Validation failure
raise HTTPException(status_code=400, detail="Item is currently reserved")

# Forbidden
raise HTTPException(status_code=403, detail="Admin privileges required")

# Unauthorized
raise HTTPException(status_code=401, detail="Invalid email or password")
```

---

## Cross-Cutting Concerns

### Logging

- Not explicitly configured; relies on FastAPI's default logging
- `DEBUG=True` enables SQLAlchemy echo for query logging

### Validation

- **Request validation:** Pydantic schemas with type hints, EmailStr, field constraints
- **Business validation:** Performed in service layer with HTTPException on failure

### Authentication

- JWT tokens via `python-jose`
- Password hashing via bcrypt
- Token expiration: 24 hours (configurable)

---

## Database

**Provider:** PostgreSQL (asyncpg driver)

**ORM:** SQLAlchemy 2.0 (async, DeclarativeBase)

**Migrations:** Alembic

**Seed Data:** Default categories seeded on startup via `init_db()`

---

## External Integrations

### Cloudinary (Image Storage)

- Configuration via environment variables
- Upload folder: `campus_marketplace/items`
- Transformations: 800x800 max, auto quality/format

### PostgreSQL

- Two connection URLs: `DATABASE_URL` (Alembic), `DATABASE_URL_POOLER` (app)
- Async connection pooling via SQLAlchemy

---

## Key Architectural Decisions

1. **Async Throughout:** All database operations use async/await for non-blocking I/O
2. **Service Layer Pattern:** Business logic isolated from route handlers
3. **Pydantic for Validation:** Schema-first request/response validation
4. **JWT for Auth:** Stateless authentication with bearer tokens
5. **Row Locking (FOR UPDATE):** Prevents race conditions on concurrent reservations
6. **5-Minute Reservation Timeout:** Auto-release reserved items to prevent marketplace stagnation
7. **Soft Deletes:** Admin removes items by setting status=SOLD (not hard delete)
8. **Hard Delete Option:** Admin can also hard delete items from database
9. **BOLA Protection:** Image upload endpoint validates seller ownership before allowing upload
10. **Timezone Handling:** Convert timezone-aware datetime to naive before storing in PostgreSQL

---

## Recent Changes (2026-02-27)

1. **Consolidated Reservation Endpoints:** All reservation operations moved to `/reservations/` router
2. **Added Admin Endpoints:** 
   - `/admin/soft-delete-item/{item_id}` - Soft delete (status=SOLD)
   - `/admin/hard-delete-item/{item_id}` - Hard delete (remove from DB)
3. **Added Owner Delete Endpoint:**
   - `DELETE /items/{item_id}` - Item owner or admin can delete
4. **Fixed DateTime Issue:** Timezone-aware datetime now converted to naive before DB insert
5. **Removed Duplicate Routes:** Block user and item delete consolidated to admin.py

*Architecture analysis: 2026-02-27*
