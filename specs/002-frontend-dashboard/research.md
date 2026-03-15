# Phase 0: Outline & Technical Research

## Polling Strategy for Real-time Status

**Decision**: Client-side polling inside a `useEffect` hook interval for the active session status endpoint.
**Rationale**: Native WebSocket support requires maintaining a stateful connection to the backend which may complicate the deployment of the FastAPI backend. Polling an asynchronous endpoint (`/api/status/:session_id`) every 3 seconds provides an acceptable UX latency while keeping infrastructure simple via stateless HTTP protocols.
**Alternatives considered**: Server-Sent Events (SSE) or WebSockets. Deemed too complex for an MVP iteration, though SSE could be a lightweight upgrade later if server-side config handles streaming connections easily.

## State Management

**Decision**: React Component State (`useState`, `useContext`) paired with caching/data-fetching hooks (e.g., SWR or React Query or standard Next.js fetch caching). No Redux required unless complexity rapidly grows.
**Rationale**: The Dashboard relies mostly on server state. Caching fetched histories and detail views avoids redundant network calls and makes UI updates instantaneous.
**Alternatives considered**: Redux. While previously mentioned in a prior chat conversation for chat functionalities, Redux may be overkill for this initial dashboard view. Kept it simple unless advanced state sharing is requested between drastically separate component branches.

## Testing Strategy for TDD

**Decision**: Jest paired with React Testing Library (RTL) for testing core component logic and utilities, and Playwright for happy path user journey E2E flows.
**Rationale**: Adhering to the project's strict Test-Driven Development (TDD) constitution, using React Testing Library encourages testing UI components as a user interacts with them rather than testing underlying implementation code. Playwright will cover the integration layer simulating real backend calls.
**Alternatives considered**: Cypress. Playwright is selected for native support of all modern browsers and speed.

## UI Styling System

**Decision**: Tailwind CSS merged with accessible Radix UI or shadcn/ui primitives.
**Rationale**: Fits the strict UI/UX Constitution requirement (Principle II). Tailwind generates premium, responsive designs quickly, and pairing it with unstyled accessible primitives provides high quality standard interactive components like dialogs, toasts, or dropdowns.
**Alternatives considered**: Standard CSS Modules. Rejected because CSS Modules do not allow for rapid shared UI standardization as easily as Tailwind's utility class mapping.
