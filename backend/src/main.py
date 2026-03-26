import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

from src.helpers.db import init_db, get_client
from src.helpers.config import Settings
from src.helpers.logging_config import get_logger, sanitize_headers, generate_request_id


logger = get_logger("app")


# ── Request / Response Logging Middleware ────────────────────────────────────
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every incoming request and its response with timing info.

    Sensitive headers (Authorization, Cookie, etc.) are automatically
    redacted by `sanitize_headers`.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = generate_request_id()
        start_time = time.perf_counter()

        # Safe header snapshot
        safe_headers = sanitize_headers(dict(request.headers))

        logger.info(
            "REQ %s | %s %s | client=%s | headers=%s",
            request_id,
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
            safe_headers,
        )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "REQ %s | %s %s | UNHANDLED EXCEPTION after %.1f ms",
                request_id,
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        log_fn = logger.info if response.status_code < 400 else logger.warning
        log_fn(
            "RES %s | %s %s | status=%s | %.1f ms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        return response


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database connection on startup."""
    logger.info("Application starting — connecting to MongoDB …")
    await init_db()
    logger.info("Database connected — application is up")
    yield
    client = get_client()
    if client:
        client.close()
    logger.info("Application shutting down, database connection closed")


# ── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Authentication System API",
    description="A simple FastAPI server with PostgreSQL connection",
    version="1.0.0",
    lifespan=lifespan,
)

# Request logging middleware (added BEFORE CORS so it wraps everything)
app.add_middleware(RequestLoggingMiddleware)

# CORS
origins = Settings().CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Authorization, Content-Type, etc.
)


from src.routes.api import api_router

# Include routers
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Authentication System API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """
    Check if the server and database are running correctly.
    """
    try:
        client = get_client()
        # Execute a simple command to verify database connectivity
        await client.admin.command('ping')
        logger.info("Health check passed — database connected")
        return {
            "status": "online",
            "database": "connected",
            "message": "System is healthy",
        }
    except Exception as e:
        logger.error("Health check FAILED — database error: %s", str(e))
        return {
            "status": "online",
            "database": f"error: {str(e)}",
            "message": "Database connection failed",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
