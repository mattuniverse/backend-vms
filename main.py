import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import create_pool, close_pool
from routers import auth, visitors, visit_requests, audit, analytics, webauthn
import logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pool()
    logger.info("Database pool created")
    yield
    await close_pool()
    logger.info("Database pool closed")


app = FastAPI(title="Vista VMS API", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS_ORIGINS is a comma-separated list of allowed frontend origins, e.g.
#   CORS_ORIGINS=https://your-app.vercel.app,https://your-app-git-main-you.vercel.app
# Localhost is always allowed too, so local development keeps working
# regardless of what's configured on Render.
_extra_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
_dev_origins = ["http://localhost:3000", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_dev_origins + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(webauthn.router)
app.include_router(visitors.router)
app.include_router(visit_requests.router)
app.include_router(audit.router)
app.include_router(analytics.router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
