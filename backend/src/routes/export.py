"""
src/routes/export.py
--------------------
REST API router for meeting export endpoints (Excel & PDF).

Endpoints
---------
GET /export/meetings/excel         — Download all completed meetings as Excel
GET /export/meetings/{id}/excel    — Download a single meeting as Excel
GET /export/meetings/{id}/pdf      — Download a single meeting as PDF
"""

import logging
from datetime import datetime, timezone

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.helpers.excel_generator import generate_all_meetings_excel, generate_single_meeting_excel
from src.models.meeting import Meeting, MeetingStatus

export_router = APIRouter(prefix="/export", tags=["export"])

logger = logging.getLogger(__name__)


def _safe_filename(text: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in text)


@export_router.get("/meetings/excel")
async def export_all_meetings_excel():
    try:
        meetings = await Meeting.find(
            Meeting.status == MeetingStatus.COMPLETED
        ).to_list()
    except Exception as exc:
        logger.error("Failed to query meetings for export: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate export. Please try again.")

    if not meetings:
        raise HTTPException(status_code=404, detail="No completed meetings available for export.")

    try:
        buf = generate_all_meetings_excel(meetings)
    except Exception as exc:
        logger.error("Failed to generate Excel export: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate export. Please try again.")

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"all_meetings_{date_str}.xlsx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@export_router.get("/meetings/{id}/excel")
async def export_single_meeting_excel(id: str):
    try:
        meeting = await Meeting.get(PydanticObjectId(id))
    except Exception:
        raise HTTPException(status_code=404, detail="Meeting not found or not yet completed.")

    if not meeting or meeting.status != MeetingStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Meeting not found or not yet completed.")

    try:
        buf = generate_single_meeting_excel(meeting)
    except Exception as exc:
        logger.error("Failed to generate single Excel export: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate export. Please try again.")

    title = _safe_filename(meeting.title or meeting.platform or "meeting")
    date_str = meeting.created_at.strftime("%Y-%m-%d")
    filename = f"meeting_{title}_{date_str}.xlsx"

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@export_router.get("/meetings/{id}/pdf")
async def export_single_meeting_pdf(id: str):
    from src.helpers.pdf_generator import generate_meeting_pdf

    try:
        meeting = await Meeting.get(PydanticObjectId(id))
    except Exception:
        raise HTTPException(status_code=404, detail="Meeting not found or not yet completed.")

    if not meeting or meeting.status != MeetingStatus.COMPLETED:
        raise HTTPException(status_code=404, detail="Meeting not found or not yet completed.")

    try:
        buf = generate_meeting_pdf(meeting)
    except Exception as exc:
        logger.error("Failed to generate PDF export: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate export. Please try again.")

    title = _safe_filename(meeting.title or meeting.platform or "meeting")
    date_str = meeting.created_at.strftime("%Y-%m-%d")
    filename = f"meeting_{title}_{date_str}.pdf"

    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
