# Phase 0: Outline & Technical Research

## LLM Output Structuring & Parsing

**Decision**: Utilize OpenAI's formal "JSON Mode" (`response_format={ "type": "json_object" }`) or Pydantic Function Calling to force the LLM to return strictly parsable associative arrays rather than relying on brittle raw text Regex matching.
**Rationale**: Early generations of LLM application development relied on asking models like GPT-3.5 to "Please format as JSON" in the prompt, which frequently failed and threw catastrophic parsing blocks. Employing the native OpenAI JSON Mode explicitly maps the requested Action Items/Decisions directly into a Python dictionary, preventing `SM-003 ParseError` instances.
**Alternatives considered**: Traditional Regex extraction over standard Markdown outputs. Rejected because models modify their bulleting and structural logic randomly, leading to massive logic overhead maintaining parsing chains.

## Temperature Control for Factual Rigor

**Decision**: Lock the execution parameter natively at `temperature=0.3` (or strictly below `0.5`).
**Rationale**: Hallucinations during meeting transcription destroy the core trust in the product (e.g., an LLM making up a "Deadline: Friday" simply because it sounds professional). A low temperature heavily constrains the probability vectors, effectively crushing creativity in favor of raw text-reduction and extraction logic. The LLM must not invent conversation that did not occur in the explicit transcript string.

## Scaling Token Windows

**Decision**: Enforce dynamic checking dividing the length of the string before passing it directly.
**Rationale**: GPT-4 handles relatively massive context lengths natively (128k output). A standard 60-minute meeting equates to roughly 8,000 words (or 11,000 tokens), which easily fits inside standard prompts without requiring a Map/Reduce or LangChain Vector split architecture dynamically.
**Alternatives considered**: Applying LangChain map-reduce splitting patterns. Rejected as overkill and too slow for a 120-second delivery target on MVP MVP requirements.
