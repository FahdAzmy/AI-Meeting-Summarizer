"""
src/routes/zoom.py
------------------
FastAPI router for Zoom Meeting SDK endpoints.

Endpoints
---------
POST /api/zoom/signature
    Generates a short-lived Zoom Meeting SDK JWT signature.
    This endpoint is **public** (no authentication required) because
    the frontend needs to call it before the SDK can join a meeting.

    The ``ZOOM_SDK_CLIENT_SECRET`` is kept on the server and is never
    included in the response; only the signed token is returned.

Security note
-------------
The endpoint does not validate that ``meeting_number`` corresponds to a
real Zoom meeting — that check is left to the Zoom SDK on the frontend.
Rate limiting should be applied at the reverse-proxy layer in production.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.settings import Config
from src.helpers.zoom_sdk import generate_zoom_signature

logger = logging.getLogger(__name__)

zoom_router = APIRouter(prefix="/zoom", tags=["Zoom Meeting SDK"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ZoomSignatureRequest(BaseModel):
    """Payload required to generate a Zoom SDK signature."""

    meeting_number: str = Field(
        ...,
        description="The numeric Zoom meeting identifier.",
        examples=["1234567890"],
    )
    role: int = Field(
        default=0,
        ge=0,
        le=1,
        description="0 = attendee, 1 = host.",
    )


class ZoomSignatureResponse(BaseModel):
    """Response containing the SDK JWT and public client ID."""

    signature: str = Field(description="Short-lived JWT for ZoomMtg.join().")
    sdk_key: str = Field(description="ZOOM_SDK_CLIENT_ID for ZoomMtg.init().")


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@zoom_router.post("/signature", response_model=ZoomSignatureResponse)
async def get_zoom_signature(body: ZoomSignatureRequest) -> ZoomSignatureResponse:
    """Generate a Zoom Meeting SDK JWT signature.

    Returns ``{"signature": "<JWT>", "sdk_key": "<CLIENT_ID>"}`` on success.

    Raises ``HTTP 500`` if ``ZOOM_SDK_CLIENT_ID`` or
    ``ZOOM_SDK_CLIENT_SECRET`` are not configured on the server.
    """
    cfg = Config()

    if not cfg.ZOOM_SDK_CLIENT_ID or not cfg.ZOOM_SDK_CLIENT_SECRET:
        logger.error(
            "get_zoom_signature: ZOOM_SDK_CLIENT_ID or ZOOM_SDK_CLIENT_SECRET "
            "not configured — cannot generate signature."
        )
        raise HTTPException(
            status_code=500,
            detail="Zoom SDK credentials not configured on the server.",
        )

    try:
        signature = generate_zoom_signature(
            meeting_number=body.meeting_number,
            role=body.role,
            sdk_key=cfg.ZOOM_SDK_CLIENT_ID,
            sdk_secret=cfg.ZOOM_SDK_CLIENT_SECRET,
        )
    except ValueError as exc:
        logger.error("get_zoom_signature: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    logger.info(
        "get_zoom_signature: signature issued for meeting_number=%s role=%d",
        body.meeting_number,
        body.role,
    )
    return ZoomSignatureResponse(signature=signature, sdk_key=cfg.ZOOM_SDK_CLIENT_ID)
