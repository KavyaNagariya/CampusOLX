from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.router import api_router
from app.db.session import engine
from app.db.init_db import init_db

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# --------------------
# CORS (for frontend later)
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# API Routers
# --------------------
app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)

# --------------------
# Startup event
# --------------------
@app.on_event("startup")
async def on_startup():
    await init_db(engine)

# --------------------
# Health check
# --------------------
@app.get("/")
async def root():
    return {
        "message": "Campus Marketplace API is running 🚀"
    }

