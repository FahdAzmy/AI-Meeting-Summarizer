"""Constants for the transcription router."""

_25_MB = 25 * 1024 * 1024
_500_MB = 500 * 1024 * 1024

MAX_AUDIO_BYTES: dict[str, int] = {
    "whisper": _25_MB,
    "deepgram": _500_MB,
    "assemblyai": _500_MB,
}
RETRY_ATTEMPTS: int = 3
FALLBACK_ORDER: dict[str, str] = {
    "whisper": "deepgram",
    "deepgram": "assemblyai",
    "assemblyai": "whisper",
}
SUPPORTED_PROVIDERS: frozenset[str] = frozenset({"whisper", "deepgram", "assemblyai"})

DEEPGRAM_LISTEN_URL = (
    "https://api.deepgram.com/v1/listen"
    "?model=nova-3&diarize=true&punctuate=true&smart_format=true"
)
