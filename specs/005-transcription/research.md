# Phase 0: Outline & Technical Research

## Provider Selection & Normalization Strategy

**Decision**: The system will support `whisper-1` via OpenAI Python SDK natively, alongside arbitrary `requests` or SDK bindings to Deepgram/AssemblyAI.
**Rationale**: OpenAI Whisper is highly accurate for generic text, but lacks intrinsic speaker diarization tags. Implementing Deepgram provides robust diarization capabilities which drastically improve transcription fidelity when creating meeting "Notes". Normalizing these disparate `JSON` dictionaries into a single `dict` (`TranscriptResult`) guarantees whatever engine succeeds, the downstream pipeline (which generates Summaries/Action Items using LLMs) doesn't have to alter its parsing heuristics.
**Alternatives considered**: Relying purely on Open-Source local Whisper binaries. Rejected due to heavy server GPU constraints required to transcribe audio quickly enough to satisfy immediate dashboard UI polling limits.

## Retry/Fallback Architecture (Resiliency)

**Decision**: Implementing custom decorators intercepting standard `requests.exceptions.HTTPError` checking for HTTP 408 (Timeout) and HTTP 429 (Rate Limit).
**Rationale**: We cannot trust external network stability. A timeout error executes an exponential mathematical delay (`sleep(min(2**attempt * 5, 20))`) giving the provider up to 20 seconds to recover under load. If a 429 is explicitly caught, the router shifts the `provider` state dynamically and attempts the secondary engine instantly to save transcription latency.
**Alternatives considered**: Tenacity package. Considered viable if decorators become too complex, though manual handling isolates the state shift logic accurately.

## File Size Bounds

**Decision**: Inject an `os.path.getsize()` check evaluating the target bytes against provider limits explicitly BEFORE opening a standard file cursor HTTP stream.
**Rationale**: OpenAI currently limits single uploads to `25MB`. An audio file surpassing this will receive a fatal error after spending significant upload bandwidth. Catching this beforehand triggers an explicit `TR-004` (Audio Too Large) failure which the orchestrator can either split or gracefully reject, sparing pipeline compute.
