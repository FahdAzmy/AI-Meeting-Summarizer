# Phase 0: Outline & Technical Research

## Database selection: MongoDB via Beanie ODM

**Decision**: The application inherently maps document structures directly reflecting standard JSON formats native to LLM architectures utilizing MongoDB and the `Beanie` ODM framework.
**Rationale**: Complex nested arrays representing objects like speaker statistics, varying numbers of action items, and large markdown string outputs fit seamlessly into MongoDB arrays natively omitting the massive overhead of mapping dozens of `SQLAlchemy` relational tables with `json.dumps()` hacks. Using `Beanie` integrates natively into FastAPI's `async/await` execution cycle, driving extreme web delivery performance.
**Alternatives considered**: Traditional SQL Databases (PostgreSQL). Rejected because forcing flexible LLM dictionaries into rigid relational schemas frequently breaks when API schemas organically adapt over time.

## Async Email Formatting strategy

**Decision**: Formatting the `MeetingReport` dynamically pushing to `aiosmtplib` for non-blocking outbound deliveries.
**Rationale**: Standard sync `smtplib` will block the specific execution thread while handshaking the mail server dynamically. Using `aiosmtplib` guarantees the entire final sequence executes smoothly avoiding blocking broader application resources. We map `alternative` multipart boundaries generating HTML structures programmatically allowing email clients to render the Decisions and Actions beautifully as distinct tables.
**Alternatives considered**: SendGrid or Mailgun API services. Rejected as out of MVP constraints, keeping costs natively strictly local utilizing baseline SMTP properties to start.

## Fault-tolerant External Storage (Google Sheets)

**Decision**: Bounding `gspread` updates specifically behind `try/except` decorators dropping explicit string values seamlessly utilizing Pandas to `.csv` dynamically upon API locks or authentication disconnects natively.
**Rationale**: Enterprise environments dictate "Data must never be lost". The MongoDB write executes unconditionally, but pushing parallel data down to secondary systems logically creates secondary failure surfaces. Bounding and cleanly failing back to local disk ensures developers can gracefully sync missed records retroactively.
