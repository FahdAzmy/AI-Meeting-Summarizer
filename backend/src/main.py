import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware

from src.helpers.db import init_db, SessionLocal
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
    """Initialize PostgreSQL connection on startup; graceful shutdown."""
    import asyncio

    logger.info("Application starting — connecting to PostgreSQL …")
    await init_db()
    logger.info("Database connected — application is up")
    yield
    # ── Graceful shutdown: wait for in-flight background tasks ────────
    logger.info("Application shutting down — waiting for background tasks …")
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if pending:
        logger.info("Waiting for %d background task(s) to finish …", len(pending))
        done, still_pending = await asyncio.wait(pending, timeout=30)
        if still_pending:
            logger.warning(
                "%d task(s) did not finish within 30 s — cancelling",
                len(still_pending),
            )
            for task in still_pending:
                task.cancel()
    logger.info("Application shutdown complete")


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
origins = [o.strip() for o in Settings().CORS_ORIGINS.split(",") if o.strip()]
if any("localhost" in o or "127.0.0.1" in o for o in origins):
    logger.warning(
        "CORS_ORIGINS contains localhost addresses — "
        "this is NOT safe for production: %s",
        origins,
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


from src.routes.api import api_router
from src.routes.auth import auth_router
from src.routes.dashboard import dashboard_router
from src.routes.export import export_router
from src.routes.members import members_router
from src.routes.notifications import notifications_router
from src.routes.teams import teams_router
from src.routes.zoom import zoom_router

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(members_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(teams_router, prefix="/api")
app.include_router(zoom_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Authentication System API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Check if the server and PostgreSQL database are running correctly."""
    try:
        from sqlalchemy import text
        if SessionLocal is None:
            raise RuntimeError("PostgreSQL SessionLocal is not initialized.")
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Health check passed — PostgreSQL connected")
        return {
            "status": "online",
            "database": "connected",
            "message": "System is healthy",
        }
    except Exception as e:
        # Log the full error server-side but NEVER expose it to clients
        logger.error("Health check FAILED — database error: %s", str(e))
        return {
            "status": "degraded",
            "database": "disconnected",
            "message": "Database connection failed",
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
