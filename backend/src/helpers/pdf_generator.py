"""
src/helpers/pdf_generator.py
-----------------------------
Pure utility module for generating structured PDF files from Meeting documents.

Uses reportlab to create professional, print-ready documents in-memory (BytesIO)
for streaming via FastAPI's StreamingResponse.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


def _get_display_title(meeting: Any) -> str:
    if meeting.title:
        return meeting.title
    platform = meeting.platform or "Meeting"
    date_str = meeting.created_at.strftime("%b %d, %Y")
    return f"{platform} — {date_str}"


def _get_participants(meeting: Any) -> str:
    stats = meeting.speaker_stats
    if not stats:
        return "N/A"
    speakers = stats.get("speakers", []) if isinstance(stats, dict) else []
    names = [s.get("speaker", "") for s in speakers if s.get("speaker")]
    return ", ".join(names) if names else "N/A"


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle", parent=base["Title"],
            fontSize=18, spaceAfter=6, textColor=colors.HexColor("#1C1917"),
        ),
        "meta": ParagraphStyle(
            "Meta", parent=base["Normal"],
            fontSize=10, textColor=colors.HexColor("#78716C"), spaceAfter=2,
        ),
        "heading": ParagraphStyle(
            "SectionHeading", parent=base["Heading2"],
            fontSize=13, spaceBefore=14, spaceAfter=6,
            textColor=colors.HexColor("#1C1917"),
        ),
        "body": ParagraphStyle(
            "BodyText", parent=base["Normal"],
            fontSize=10, leading=14, spaceAfter=4,
            textColor=colors.HexColor("#44403C"),
        ),
        "bullet": ParagraphStyle(
            "BulletText", parent=base["Normal"],
            fontSize=10, leading=14, leftIndent=12, spaceAfter=3,
            textColor=colors.HexColor("#44403C"),
        ),
        "transcript": ParagraphStyle(
            "Transcript", parent=base["Normal"],
            fontSize=9, leading=12, spaceAfter=2,
            textColor=colors.HexColor("#57534E"),
        ),
    }


def generate_meeting_pdf(meeting: Any) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )

    styles = _build_styles()
    story: list[Any] = []

    # Header
    title = _get_display_title(meeting)
    story.append(Paragraph(title, styles["title"]))

    date_str = meeting.created_at.strftime("%B %d, %Y at %H:%M UTC")
    duration = f"{meeting.duration_minutes} minutes" if meeting.duration_minutes else "N/A"
    platform = meeting.platform or "Unknown"
    story.append(Paragraph(f"Date: {date_str} &nbsp;|&nbsp; Duration: {duration} &nbsp;|&nbsp; Platform: {platform}", styles["meta"]))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#D6D3D1")))
    story.append(Spacer(1, 4 * mm))

    # Participants
    participants = _get_participants(meeting)
    if participants != "N/A":
        story.append(Paragraph("Participants", styles["heading"]))
        story.append(Paragraph(participants, styles["body"]))

    # Summary
    if meeting.summary:
        story.append(Paragraph("Summary", styles["heading"]))
        for line in meeting.summary.split("\n"):
            stripped = line.strip()
            if stripped:
                story.append(Paragraph(stripped, styles["body"]))

    # Decisions
    if meeting.decisions:
        story.append(Paragraph("Key Decisions", styles["heading"]))
        for decision in meeting.decisions:
            story.append(Paragraph(f"• {decision}", styles["bullet"]))

    # Action Items
    if meeting.action_items:
        story.append(Paragraph("Action Items", styles["heading"]))
        table_data = [["Assignee", "Task", "Deadline"]]
        for item in meeting.action_items:
            table_data.append([
                item.get("assignee", "—"),
                item.get("task", "—"),
                item.get("deadline", "—") or "—",
            ])

        table = Table(table_data, colWidths=[80, 280, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1C1917")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D6D3D1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAF9")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)

    # Follow-up
    if meeting.follow_up:
        story.append(Paragraph("Follow-up Items", styles["heading"]))
        for item in meeting.follow_up:
            story.append(Paragraph(f"• {item}", styles["bullet"]))

    # Transcript
    if meeting.transcript:
        story.append(Paragraph("Transcript", styles["heading"]))
        for line in meeting.transcript.split("\n"):
            stripped = line.strip()
            if stripped:
                story.append(Paragraph(stripped, styles["transcript"]))

    doc.build(story)
    buf.seek(0)
    return buf
