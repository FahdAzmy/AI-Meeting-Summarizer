# Phase 0: Outline & Technical Research

## Bounding Blocking Operations (Selenium vs Asyncio)

**Decision**: Using standard `asyncio.to_thread()` mappings around the profoundly explicit blocking libraries natively built within the `MeetingAccess` and `AudioCapture` classes completely limiting standard REST hangs.
**Rationale**: Python's native `asyncio` execution loops completely crash or hang globally if an engineered thread introduces blocking boundaries logically (like `time.sleep()`, or synchronous Selenium GUI drivers scanning HTML). While the web server `FastAPI` manages asynchronous HTTP responses perfectly natively, pushing Selenium into `asyncio.to_thread()` actively spawns it completely within an external OS thread pool accurately returning control seamlessly preventing core server limits stalling explicitly.
**Alternatives considered**: Traditional `.celery` task structures. Rejected as too high an infrastructure load (requires running Redis & Celery Workers) for an MVP natively capable of surviving through internal OS threaded pools reliably.

## State Mutability and Frontend Updates

**Decision**: Real-time MongoDB document mutation at every sequence phase strictly calling `meeting.save()` dynamically via the Beanie ODM structure natively.
**Rationale**: If the application crashes halfway through a meeting, the Database holds exactly how far the robot natively progressed organically rather than being caught in a phantom "In Progress" execution state permanently structurally mapping errors natively.
**Alternatives considered**: Maintaining states in memory organically. Rejected because active system shutdowns crash local RAM implicitly leaving user interfaces completely disjointed without database alignment.
