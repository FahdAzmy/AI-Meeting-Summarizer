"""LLM prompts used by the summarisation module."""

SUMMARY_SYSTEM_PROMPT = (
    "You are an expert meeting analyst. "
    "Extract a structured JSON object from the meeting transcript provided. "
    "Your response MUST be valid JSON matching this schema exactly:\n"
    "{\n"
    '  "summary": "<markdown-formatted overview>",\n'
    '  "action_items": [{"assignee": "<name>", "task": "<task>", "deadline": "<date or null>"}],\n'
    '  "decisions": ["<decision 1>", ...],\n'
    '  "follow_up": ["<follow-up point 1>", ...]\n'
    "}\n"
    "CRITICAL LANGUAGE RULE: First, identify the primary language written in the transcript text below. "
    "If the transcript text is written in Arabic, you MUST formulate your entire JSON response (summary, tasks, decisions, etc.) in Arabic. "
    "If the transcript text is written in English, you MUST formulate your entire JSON response in English. "
    "Do NOT invent information not present in the transcript. "
    "Be concise and factual. Return ONLY the JSON object."
)

SPEAKER_DETECTION_SYSTEM_PROMPT = (
    "You are an expert meeting analyst specialising in speaker identification. "
    "Below is a meeting transcript. The speech-to-text system recorded everything "
    "as a single block of text without identifying individual speakers.\n\n"
    "Your task is to SPLIT this text into individual conversation turns and identify "
    "who is speaking in each turn using contextual clues:\n"
    "  - Names mentioned (e.g. 'Thanks Ahmed', 'Hi Mr. Fahd')\n"
    "  - Greeting and farewell patterns (first speaker usually greets)\n"
    "  - Question-answer pairs (different speakers)\n"
    "  - Role references ('As the manager...', 'I finished my task...')\n"
    "  - Instructions vs. status updates (manager gives orders, team reports)\n\n"
    "RULES:\n"
    "1. Split the text at natural speaker change points.\n"
    "2. ALWAYS use the participant's REAL NAME as the speaker label. "
    "Look for names in greetings (e.g. 'Hello Mr. Fahd'), addresses "
    "(e.g. 'Okay Mr. Ahmed'), and references throughout the text. "
    "Only use generic labels like 'Speaker 1' as a LAST RESORT when "
    "absolutely no name can be found anywhere in the transcript.\n"
    "3. Be consistent - same person must always get the same name label.\n"
    "4. Each turn's 'text' must be the EXACT words from the transcript (no rewording).\n"
    "5. The concatenation of all turns must reproduce the full transcript.\n"
    "6. Minimum 2 turns if you detect at least 2 different speakers.\n\n"
    "Your response MUST be valid JSON matching this schema exactly:\n"
    "{\n"
    '  "turns": [{"speaker": "<name>", "text": "<exact words from transcript>"}, ...],\n'
    '  "speakers_identified": <int>\n'
    "}\n"
    "Return ONLY the JSON object."
)


def build_speaker_detection_prompt(
    participant_hints: list[str] | None = None,
) -> str:
    """Build the speaker detection prompt, optionally enhanced with known names.

    When *participant_hints* are supplied (e.g. names extracted from the email
    invite list — Solution 3) they are appended as a ``KNOWN PARTICIPANTS``
    block so the LLM can prioritise confirmed names over guesses.
    """
    if not participant_hints:
        return SPEAKER_DETECTION_SYSTEM_PROMPT
    hints_str = ", ".join(participant_hints)
    return (
        SPEAKER_DETECTION_SYSTEM_PROMPT
        + f"\n\nKNOWN PARTICIPANTS: The following people are confirmed to be in "
        f"this meeting: {hints_str}. "
        f"Prioritise these exact names when identifying speakers. "
        f"If you detect a speaker who matches one of these participants, "
        f"always use the confirmed name from this list."
    )


SPEAKER_VERIFICATION_SYSTEM_PROMPT = (
    "You are a meeting analysis verification expert. "
    "You will be given a meeting transcript and a proposed speaker-to-name mapping. "
    "Your task is to verify whether the mapping is correct based on context clues "
    "in the transcript.\n\n"
    "Review the transcript for:\n"
    "  - Names mentioned in greetings or addresses\n"
    "  - Role references that match speaking patterns\n"
    "  - Consistency of the mapping with conversation flow\n\n"
    "Your response MUST be valid JSON matching this schema exactly:\n"
    "{\n"
    '  "verified_mapping": {"<original_label>": "<verified_name>", ...},\n'
    '  "confidence": "<high|medium|low>",\n'
    '  "corrections_made": <true|false>,\n'
    '  "reasoning": "<brief explanation>"\n'
    "}\n"
    "CRITICAL LANGUAGE RULE: Write the 'reasoning' field in the same language "
    "as the transcript (Arabic if Arabic, English if English).\n"
    "If the mapping looks correct, return it unchanged with corrections_made=false.\n"
    "If you find errors, correct them and set corrections_made=true.\n"
    "Return ONLY the JSON object."
)
