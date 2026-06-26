"""Pure HTML rendering for output-storage summary emails."""

from __future__ import annotations

from typing import Any

from modules._output_storage.constants import (
    EMAIL_FALLBACK_TEXT,
    NO_ACTION_ITEMS_HTML,
    NO_DECISIONS_HTML,
    NO_SUMMARY_TEXT,
)
from modules._output_storage.templates import load_partial, load_template
from modules._output_storage.types import MeetingReportPayload


def render_email_body(report: MeetingReportPayload | dict[str, Any]) -> str:
    """Render MeetingReport data as the existing styled HTML email body."""
    summary: str = report.get("summary", NO_SUMMARY_TEXT)
    decisions: list = report.get("decisions", [])
    action_items: list = report.get("action_items", [])
    follow_up: list = report.get("follow_up", [])
    speaker_stats = report.get("speaker_stats")

    if decisions:
        items_html = "".join(f"<li>{d}</li>" for d in decisions)
        decisions_html: str = load_partial("list").format_map({"items": items_html})
    else:
        decisions_html = NO_DECISIONS_HTML

    if action_items:
        rows = "".join(
            load_partial("action_item_row").format_map(
                {
                    "assignee": item.get("assignee", EMAIL_FALLBACK_TEXT),
                    "task": item.get("task", EMAIL_FALLBACK_TEXT),
                    "deadline": item.get("deadline", EMAIL_FALLBACK_TEXT),
                }
            )
            for item in action_items
        )
        action_table: str = load_partial("action_table").format_map({"rows": rows})
    else:
        action_table = NO_ACTION_ITEMS_HTML

    if follow_up:
        items_html = "".join(f"<li>{f}</li>" for f in follow_up)
        follow_up_section: str = load_partial("follow_up").format_map(
            {"items": items_html}
        )
    else:
        follow_up_section = ""

    speaker_html: str = ""
    if speaker_stats:
        speakers: list = speaker_stats.get("speakers", [])
        most_active: str = speaker_stats.get("most_active_speaker", "")
        rows = "".join(
            load_partial("speaker_row").format_map(
                {
                    "speaker": s.get("speaker", EMAIL_FALLBACK_TEXT),
                    "speaking_time": f"{s.get('total_speaking_time_sec', 0):.0f}",
                    "share": f"{s.get('percentage_of_meeting', 0):.1f}",
                    "turns": s.get("number_of_turns", 0),
                }
            )
            for s in speakers
        )
        most_active_line = (
            f"<p style='margin-top:8px;color:#6b7280'>"
            f"Most active: <strong>{most_active}</strong></p>"
            if most_active
            else ""
        )
        speaker_html = load_partial("speaker").format_map(
            {
                "rows": rows,
                "most_active_line": most_active_line,
            }
        )

    return load_template().format_map(
        {
            "summary": summary,
            "decisions_html": decisions_html,
            "action_table": action_table,
            "follow_up_section": follow_up_section,
            "speaker_html": speaker_html,
        }
    )
