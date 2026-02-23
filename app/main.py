from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.router import api_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# --------------------
# CORS Configuration
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
# Health check
# --------------------
@app.get("/")
async def root():
    return {
        "message": "Campus Marketplace API is running 🚀"
    }