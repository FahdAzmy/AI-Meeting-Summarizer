"""Constants for the output storage module."""

from __future__ import annotations

from pathlib import Path

BACKEND_DATABASE = "database"
VALID_BACKENDS: frozenset[str] = frozenset({BACKEND_DATABASE})

EMAIL_SUBJECT = "Your Meeting Summary \u2013 AI Meeting Summarizer"
EMAIL_HTML_SUBTYPE = "html"
EMAIL_CHARSET = "utf-8"
EMAIL_FALLBACK_TEXT = "\u2014"

NO_SUMMARY_TEXT = "No summary available."
NO_DECISIONS_HTML = "<p><em>No decisions recorded.</em></p>"
NO_ACTION_ITEMS_HTML = "<p><em>No action items recorded.</em></p>"

TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent / "templates"
TEMPLATE_PATH: Path = TEMPLATES_DIR / "email_meeting_summary.html"
PARTIAL_PATHS: dict[str, Path] = {
    "list": TEMPLATES_DIR / "partials" / "list.html",
    "action_table": TEMPLATES_DIR / "partials" / "action_items_table.html",
    "action_item_row": TEMPLATES_DIR / "partials" / "action_item_row.html",
    "follow_up": TEMPLATES_DIR / "partials" / "follow_up_section.html",
    "speaker": TEMPLATES_DIR / "partials" / "speaker_highlights.html",
    "speaker_row": TEMPLATES_DIR / "partials" / "speaker_row.html",
}
