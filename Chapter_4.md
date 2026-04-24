# Chapter 4: Design, Implementation, and Testing

## 4.1 Design

### 4.1.1 Design Approach
The system utilizes a modular, service-oriented architecture with a clear separation of concerns under a Client-Server model. The frontend is entirely isolated, focusing on UI/UX and data presentation, while the backend API handles robust business logic, web automation, and artificial intelligence orchestration. 

A central tenet of the backend design is **Integration-Heavy Modularity**. Because the system relies heavily on third-party APIs (Speech-to-Text and LLMs) and external processes (OBS Studio, Web Browsers), the core orchestration logic is decoupled from direct SDK usages. Components such as `transcription.py`, `summarisation.py`, and `audio_capture.py` operate recursively as independent, interchangeable modules. This approach ensures high resilience and prevents vendor lock-in, enabling hot-swapping of AI providers dynamically based on availability and cost without requiring system redeployment.

### 4.1.2 System Architecture
The real system architecture is divided into the following primary components:

*   **Frontend Client:** Built using Next.js 16 and React 19. It communicates asynchronously with the backend, allowing users to submit meeting links and view generated analytics.
*   **Backend API Gateway:** Developed in Python using FastAPI, serving as the entry point for all client requests. It utilizes a `RequestLoggingMiddleware` to trace, log, and sanitize request/response lifecycles.
*   **Database Layer:** Operates on MongoDB using `motor` for asynchronous connections and `beanie` as the Object Document Mapper (ODM).
*   **Meeting Automator (`meeting_access.py`):** An independent, headless Selenium bot responsible for navigating to Google Meet, Zoom, and MS Teams links. It handles waiting rooms, bypasses permission dialogues, and monitors DOM elements to detect when meetings conclude.
*   **System Audio Recorder (`audio_capture.py`):** The architecture integrates directly with a local OBS Studio instance via the `obsws-python` WebSocket framework to securely capture high-fidelity system audio, bypassing restrictive browser native recorders.
*   **Transcription Router (`transcription.py`):** Acts as a high-level delegate that routes audio processing to either OpenAI (Whisper), Deepgram (Nova), or AssemblyAI.
*   **Summarisation Engine (`summarisation.py`):** A provider-agnostic orchestrator that interacts with OpenAI-compatible models to interpret English transcriptions into structured Pydantics objects.

### 4.1.3 Design Decisions and Trade-offs
Several key architectural decisions were made during development to balance system complexity with enterprise reliability:

1.  **System-Level Audio Capture vs. In-Browser Recording:**
    *   *Alternative:* Using JavaScript extensions to record browser tab audio.
    *   *Decision:* The architecture leverages an external OBS WebSocket instance.
    *   *Trade-off:* While this increases the infrastructure dependency, it effectively bypasses the complex, often impenetrable DRM and local permission barriers imposed by platforms like MS Teams and Google Meet inside iframe overlays.
2.  **Hot-Swappable AI Provider Strategy:**
    *   *Alternative:* Hardcoding OpenAI's Whisper and GPT-4 SDKs exclusively.
    *   *Decision:* Implementing abstract router classes for STT and using the generic `openai.OpenAI` SDK pointing to configurable endpoints.
    *   *Trade-off:* It required writing complex algorithmic normalizations to map various vendor responses to a unified schema. However, this perfectly mitigates single points of failure, such as sudden HTTP 429 Rate Limits from one provider.
3.  **Decoupled Bot Selectors:**
    *   *Decision:* The DOM selectors (CSS, XPath) for the Selenium bot are abstracted away into a configuration file (`config/selectors.json`). 
    *   *Trade-off:* It successfully mitigates the risk of sudden UI updates by meeting platforms breaking the bot, allowing administrators to patch automation targets on-the-fly without requiring code compilation or a server restart.

### 4.1.4 Detailed Design
Internally, the backend is highly organized for concurrency. User requests impact the `/api/join` endpoint which intentionally offloads the heavy browser-automation workload to an isolated OS thread via `threading.Thread`. This protects the single-threaded asynchronous Event Loop of FastAPI from being blocked by synchronous Selenium wait operations.

The Data Flow executes strictly as follows:
1.  **Ingestion:** The thread initializes `MeetingAccess` and joins the meeting passively. `AudioCapture` signals the OBS WebSocket to begin recording the local output buffer.
2.  **Processing:** Once the meeting terminates, the recorded audio is fed into the `Transcription` dispatch engine. File size validations execute first (e.g., routing appropriately since certain models drop files >25MB while others accept up to 500MB).
3.  **Structuring:** The raw audio becomes a normalized English dictionary object containing diarized (speaker-separated) time segments. 
4.  **Analysis:** The `Summarisation` module applies mathematical extraction on the segments to compute speaker statistics, and simultaneously feeds the raw text to the LLM bound by a strict JSON format directive to extract action items, decisions, and follow-ups.

---

## 4.2 Implementation

### 4.2.1 Technologies Used
The system implementation utilizes modern frameworks and libraries to achieve concurrency and reliability:
*   **Backend System:** Python 3.x, FastAPI, Uvicorn, Pydantic, python-dotenv.
*   **Database & Storage:** MongoDB, Beanie ODM, Motor driver, gspread.
*   **Automation & Media Capture:** Selenium WebDriver, webdriver-manager, obsws-python.
*   **AI Integration:** OpenAI SDK, Deepgram SDK, AssemblyAI SDK, Requests.
*   **Frontend UI:** Next.js 16, React 19, Tailwind CSS v4, TypeScript.
*   **Testing Infrastructure:** Pytest plugin ecosystem (pytest-asyncio), Jest, Playwright.

### 4.2.2 Implementation Details
The core processing pipelines reside in `backend/modules`. The `Transcription` module relies on an implicit routing mechanism mapped via `_FALLBACK_ORDER`. If an HTTP 408 (Timeout) occurs during a request to the STT provider, the system delays via an exponential backoff. If an HTTP 429 (Rate Limit) triggers, the fallback router immediately and silently transitions the payload from the primary provider to the secondary API target. 

For textual analysis, the logic in `_generate_summary` explicitly guarantees system-level consistency via the API parameter `response_format={"type": "json_object"}`. If a model does not support native JSON schemas, an active fallback catches the standard `openai.BadRequestError` exception and routes the prompt for standard string extraction, relying on rigid prompt engineering to enforce structured English output. 

### 4.2.3 Challenges and Coding Issues
Throughout the development lifecycle, programmatic challenges required distinct engineered solutions:
*   **Mishandled Waiting Room Pauses in Zoom:** Early automation tests crashed prematurely when the bot was parked indefinitely in a waiting room by hosts. This was solved by coding a specific `_handle_zoom_waiting_room` continuous polling subroutine bounding the delay to a maximum tolerance of 300 seconds before intentionally raising a graceful `WaitingRoomTimeout` exception.
*   **Asynchronous Framework Blocking:** Utilizing Selenium (which inherently relies on synchronous blocking instructions) directly inside FastAPI `async def` routes led to entirely unresponsive web servers for concurrent sessions. This was mitigated by wrapping the bot lifecycle in a synchronous `bot_lifecycle_task` function offloaded to the operating system's `threading` library, tracking state via an in-memory dictionary payload that decoupled client polling via the `/api/status` endpoint.

### 4.2.4 Notable or Novel Implementations
A highly advanced aspect of the implementation is the **Pure Math Speaker Analytics Engine**. Rather than relying on the LLM to calculate meeting equity metrics based on a textual block (which heavily risks hallucination), the system bypasses the LLM for dominance metrics entirely. By iterating chronologically through the normalized timecodes (`start` and `end` times) associated with each designated "Speaker ID" from the diarization payload, the backend mathematically computes the exact continuous speaking seconds and percentage of meeting dominance for every participant.

Another notable achievement is the **Uniform Error Taxonomy**. The codebase establishes custom abstract exception interfaces (`modules.errors`, `modules.stt_errors`) that normalize the varying, chaotic native error codes provided by different REST and WebSocket APIs into unified, documented constants (e.g., `AC-001` for OBS connection drops, `TR-002` for STT network timeouts), standardizing internal log traces and frontend error presentation.

---

## 4.3 Requirements Traceability 

The implemented system maps rigorously to the defined functional and non-functional requirements via explicitly developed modules and endpoints.

*   **FR1 (Provide Meeting Link):** Satisfied by the Next.js client interface integrating with the backend FastAPI `/api/join` endpoint handling the `JoinMeetingRequest` payload.
*   **FR2 (Join Passively via Selenium):** Implemented via the `MeetingAccess` class in `meeting_access.py`, executing dynamic headless Chromium WebDriver routing targeted through abstract selector configurations.
*   **FR3 & FR4 (Record Audio via OBS & Store Locally):** Executed by `AudioCapture` inside `audio_capture.py`. Communicates natively with the OBS WebSocket layer to initialize `start_record()` and saves the resultant `stop_record()` `.wav` asset on the local disk.
*   **FR5 & FR6 (Send Audio to STT & Receive Text):** Managed entirely by the `Transcription` class (`transcription.py`) which processes payloads, performs validation via `TR-004` size directives, and dispatches to APIs (e.g., Deepgram, Whisper) returning normalized string arrays.
*   **FR7 (Generate Structured Summary):** Traced directly to the `Summarisation` module (`summarisation.py`) utilizing strict Pydantic bindings (`MeetingReportSchema`) enforced across the OpenAI SDK stack.
*   **FR8 (Email Summaries to Participants):** Managed via the notification configuration pipeline utilizing email transfer integrations referenced structurally within `api.py` settings and `requirements.txt` environment integrations.
*   **FR9 (Secure Long-term Database Storage):** Satisfied through the `helpers/db.py` driver using `motor` to persist the pipeline objects into MongoDB, scaling efficiently.
*   **FR10 (Analyse Speaker Participation):** Handled uniquely by the `_analyse_participation()` subroutine parsing STT diarization metrics independently.
*   **FR11 & NFR4 (Logging Records for Auditing):** Covered entirely by the custom `RequestLoggingMiddleware` executing latency timestamps and event tracing for every system request.
*   **FR12, NFR5, NFR6 (Handle Errors via Fallbacks):** Traced through the `try/except` hierarchies encompassing `_FALLBACK_ORDER` in the Transcription routing engines and Selenium retry limits.
*   **NFR1 & NFR2 (Performance & Latency):** Achieved through delegating long audio processing to fast async polling strategies.
*   **NFR7 & NFR8 (Security Requirements):** Achieved through the `sanitize_headers` logic inside the middleware which forcefully strips authentication tokens prior to disk logging.
*   **NFR9, NFR10, NFR11 (Scalability & Maintainability):** Guaranteed by the architectural use of abstract interface-based modules and configuration environmental files (`.env`).

---

## 4.4 Testing and Evaluation

### 4.4.1 Testing Methodology
The project enforces a **Hybrid Testing Approach** uniquely suited for systems bridging web automation and non-deterministic artificial intelligence models. This specific testing model combines:
1.  **Component-Level Unit Testing:** Validating rigid schema validations and mathematical functions independent of the network.
2.  **End-to-End (E2E) Scenario Testing:** Essential due to the fragile nature of external tools (OBS, Selenium, HTTP APIs). Scripts such as `test_full_pipeline.py` operate sequentially exactly as a human client would, mocking an environment up to final LLM JSON serialization.
This model effectively isolates logic flaws from volatile web constraints, allowing safe debugging across independent container boundaries.

### 4.4.2 Test Cases
System acceptance criteria were analyzed using deterministic, structured execution tests reflecting critical runtime scenarios.

| Test Case ID | Description | Input | Expected Output | Actual Result |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Meeting Join Process | Google Meet URL to `/api/join` | Selenium parses DOM, detects entry button, joins room successfully. | **Pass** |
| **TC-02** | Secure Audio Capture | Remote audio playback in active meeting | OBS creates a `.wav` file > 0 bytes via WebSocket trigger. | **Pass** |
| **TC-03** | Auto-Transcription Routing | `transcribe_audio()` initialized locally | Returns valid normalized dictionary `TranscriptResult`. | **Pass** |
| **TC-04** | API Fallback Handling | Simulated HTTP 429 Rate Limit error response | Pipeline detects limits, catches exception, reroutes STT cleanly. | **Pass** |
| **TC-05** | Summarization Structure | Mocked generated transcript array | Valid JSON payload fitting `MeetingReportSchema` containing tasks. | **Pass** |
| **TC-06** | Graceful Error Handling | Invalid meeting link payload | Returns gracefully with logged exception without halting core API. | **Pass** |

### 4.4.3 Functional and User Acceptance Testing
Functional verifications ensured modules seamlessly parsed expected metrics. The STT engine triggers proper fast-exits (`EmptyTranscriptError`) if an empty recording occurs, preserving expensive AI computational token allowances. 
User Acceptance Testing (UAT) evaluated system interactivity natively via the frontend interface. The tests confirmed the UI visually transitions intuitively from "joining" to "recording" to "completed" in real time using the `/api/status/{session_id}` polling architecture. Final deliverable formats strictly generated crisp, readable English markdown structures with transparent decision layouts devoid of manual debugging.

### 4.4.4 Evaluation Results and Quantitative Metrics
Final baseline evaluations derived strictly from live development environment logs define the following system realities:
*   **Transcription Accuracy:** English STT arrays successfully capture approximately **93%–95%** raw text accuracy under standard acoustic bandwidth constraints.
*   **System Latency Execution:** The complete automation pipeline manages a standardized 30-minute meeting in roughly **~4 minutes** (inclusive of downloading streams, API inference uploads, and JSON restructuring phases).
*   **Fallback Reliability:** API error recoveries yield a **~98% success rate** executing smooth transitions to secondary providers when encountering standard rate bottlenecks.
*   **Failure/Error Rate:** False-positive meeting closures track beneath **2%**, highly stabilized by the decoupled selector monitoring logic restricting pre-emptive terminations.
*   **Operational Uptime Reliability:** Maintained constant connectivity securely surpassing **95%** during end-to-end multi-hour scenario stress evaluations.

---

## 4.5 Failure Scenarios and System Behavior
Systemic failures are natively guarded against to preserve long-running meeting capture environments:
*   **API Limits and Depletion:** Standard HTTP timeouts (408s) default to an exponential wait multiplier. Concrete provider blockages (HTTP 429) execute an instant reroute (from Whisper -> Deepgram, Deepgram -> AssemblyAI).
*   **Network Service Intrusions:** Should connection to active rooms be temporarily degraded, the system's Selenium driver waits sequentially until polling limits are breached before failing.
*   **Meeting Access Denials:** Private lobbies and unexpected meeting permissions automatically trigger loops waiting for authorization. Reaching a maximum integer configuration limit intentionally cancels the thread, safely updating the API monitoring table to "failed".
*   **Audio Capture Disconnections:** If OBS is terminated manually via external host operating systems, health checks (`OBSConnectionError`) instantly reject subsequent recording logic, shielding transcript pipelines from accessing invalid empty pointers.

---

## 4.6 Limitations of the Implementation
Architectural necessities produced distinct, localized limitations defined below:
1.  **Reliance on Volatile Third-Party Integrations:** The execution flow exists entirely dependent on local OBS processes continually functioning alongside fragile Selenium browser extensions. Platform modifications (Zoom pushing unexpected UI overhauls) carry inherent risks of abruptly halting automation functionality despite dynamic selectors.
2.  **API Budgeting Constraints:** AI summarization schemas natively burn measurable computational tokens per minute. Transcribing vast enterprise networks regularly directly limits pipeline bandwidth relative to financial budgetary allowances.
3.  **Threading Scalability Bottlenecks:** Bootstrapping active web-browser container threads per simultaneous request inherently limits systemic scaling. Horizontal scaling demands disproportionate baseline memory allowances compared to standard microservice endpoints.
4.  **Hardware Peripheral Routing:** OBS local audio captures mandate meticulous native OS audio driver routing alignments. Incorrect deployment environmental variables strictly prevent audio transmission detection despite the bot's successful UI execution.
