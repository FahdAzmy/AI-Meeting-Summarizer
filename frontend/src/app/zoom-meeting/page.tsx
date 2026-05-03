"use client";

/**
 * app/zoom-meeting/page.tsx
 * -------------------------
 * Dedicated background page that joins a Zoom meeting using the
 * official Zoom Meeting SDK.
 *
 * This page is opened by the pipeline orchestrator in a background browser
 * tab. The user never interacts with it directly; it only needs to:
 *   1. Parse the meeting link from the URL search params.
 *   2. Fetch a JWT signature from the backend.
 *   3. Initialise the Zoom SDK and join the meeting as "AI Summarizer".
 *   4. Listen for the meeting-end event (onLeave) and notify the backend.
 *
 * URL format expected by the orchestrator:
 *   /zoom-meeting?link=https%3A%2F%2Fzoom.us%2Fj%2F1234567890%3Fpwd%3Dabc
 *   /zoom-meeting?link=...&meeting_id=<mongo_id>
 *
 * The `meeting_id` query parameter is the MongoDB document ID that the
 * backend uses to advance the pipeline status to RECORDING.
 *
 * IMPORTANT: The Zoom Client View SDK creates its own #zmmtg-root element
 * via prepareWebSDK().  This page must NOT render a manual <div id="zmmtg-root">.
 * Doing so creates a duplicate that hides the SDK's real UI.
 */

import "@zoom/meetingsdk/dist/css/bootstrap.css";
import "@zoom/meetingsdk/dist/css/react-select.css";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  parseZoomUrl,
  fetchZoomSignature,
  initZoomClient,
  joinZoomMeeting,
} from "@/lib/zoom";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Status =
  | "idle"
  | "parsing"
  | "fetching_token"
  | "initialising_sdk"
  | "joining"
  | "in_meeting"
  | "meeting_ended"
  | "error";

// ---------------------------------------------------------------------------
// API base (same as lib/zoom.ts — reads env var or falls back to localhost)
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ZoomMeetingPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const hasJoined = useRef(false); // prevents double-join in Strict Mode

  // ── Derived query params ─────────────────────────────────────────────────
  const meetingLink = searchParams.get("link") ?? "";
  const meetingId = searchParams.get("meeting_id") ?? "";

  // ── Main join flow ───────────────────────────────────────────────────────
  useEffect(() => {
    if (!meetingLink || hasJoined.current) return;
    hasJoined.current = true;

    void (async () => {
      try {
        // Step 1: Parse URL
        setStatus("parsing");
        console.info("[ZoomMeetingPage] Parsing URL:", meetingLink);
        const details = parseZoomUrl(meetingLink);
        if (!details) {
          throw new Error(`Invalid Zoom URL: "${meetingLink}"`);
        }
        console.info("[ZoomMeetingPage] Parsed meeting:", details.meetingNumber, "passcode:", details.passcode ? "****" : "(none)");

        // Step 2: Fetch signature from backend
        setStatus("fetching_token");
        console.info("[ZoomMeetingPage] Fetching signature from backend…");
        const { signature, sdk_key } = await fetchZoomSignature(
          details.meetingNumber,
          0 // role: 0 = attendee
        );
        console.info("[ZoomMeetingPage] Got signature (length:", signature.length, ") sdk_key:", sdk_key.substring(0, 8) + "…");

        // Step 3: Initialise SDK
        setStatus("initialising_sdk");
        console.info("[ZoomMeetingPage] Initialising Zoom SDK…");
        await initZoomClient(sdk_key, "AI Summarizer");
        console.info("[ZoomMeetingPage] SDK initialised successfully");

        // Step 4: Register end-of-meeting listener BEFORE joining
        //         (US2 – Native Meeting End Detection)
        const { ZoomMtg } = await import("@zoom/meetingsdk");
        ZoomMtg.inMeetingServiceListener("onMeetingStatus", (data: { meetingStatus: number }) => {
          console.info("[ZoomMeetingPage] onMeetingStatus:", data.meetingStatus);
          // meetingStatus === 3 means "disconnected" in the Zoom Web SDK
          if (data.meetingStatus === 3) {
            handleMeetingEnd(meetingId);
          }
        });

        // Step 5: Join the meeting
        setStatus("joining");
        console.info("[ZoomMeetingPage] Joining meeting…");
        await joinZoomMeeting({
          signature,
          sdkKey: sdk_key,
          meetingNumber: details.meetingNumber,
          passcode: details.passcode,
          userName: "AI Summarizer",
        });

        setStatus("in_meeting");
        console.info("[ZoomMeetingPage] Successfully joined meeting:", details.meetingNumber);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        console.error("[ZoomMeetingPage] Join failed:", message, err);
        setStatus("error");
        setErrorMessage(message);

        // Notify backend of failure so the pipeline can be marked FAILED
        if (meetingId) {
          await notifyBackend(meetingId, "failed").catch(() => {});
        }
      }
    })();
  }, [meetingLink, meetingId]);

  // ── Event handler: meeting ended (US2) ───────────────────────────────────
  async function handleMeetingEnd(id: string) {
    console.info("[ZoomMeetingPage] Meeting ended — notifying backend.");
    setStatus("meeting_ended");
    if (id) {
      await notifyBackend(id, "recording").catch((err) => {
        console.error("[ZoomMeetingPage] Failed to notify backend:", err);
      });
    }
  }

  // ── Backend notification (US2) ───────────────────────────────────────────
  async function notifyBackend(id: string, newStatus: string) {
    await fetch(`${API_BASE}/meetings/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
  }

  // ── Render ───────────────────────────────────────────────────────────────
  // NOTE: We do NOT render a <div id="zmmtg-root"> here.
  // The Zoom Client View SDK creates its own #zmmtg-root automatically
  // via ZoomMtg.prepareWebSDK(). Adding a second one creates a duplicate
  // element that hides the SDK's real meeting UI.
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        paddingTop: "12px",
        background: "#0a0a0a",
        color: "#e5e5e5",
        fontFamily: "system-ui, sans-serif",
        fontSize: "14px",
        gap: "12px",
        zIndex: 0,  // Stay below the Zoom SDK overlay (z-index: 100+)
      }}
    >
      {/* Status indicator */}
      <StatusBadge status={status} />

      {/* Error message */}
      {status === "error" && (
        <p
          style={{
            color: "#f87171",
            maxWidth: "480px",
            textAlign: "center",
            margin: 0,
          }}
        >
          {errorMessage}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: Status badge
// ---------------------------------------------------------------------------

const STATUS_LABELS: Record<Status, string> = {
  idle: "Initialising…",
  parsing: "Parsing meeting link…",
  fetching_token: "Fetching authorisation token…",
  initialising_sdk: "Loading Zoom SDK…",
  joining: "Joining meeting…",
  in_meeting: "In meeting — AI Summarizer is listening",
  meeting_ended: "Meeting ended — processing recording…",
  error: "Error joining meeting",
};

function StatusBadge({ status }: { status: Status }) {
  const isError = status === "error";
  const isSuccess = status === "in_meeting" || status === "meeting_ended";

  return (
    <div
      style={{
        padding: "8px 16px",
        borderRadius: "9999px",
        background: isError
          ? "rgba(239,68,68,0.15)"
          : isSuccess
          ? "rgba(34,197,94,0.15)"
          : "rgba(99,102,241,0.15)",
        border: `1px solid ${
          isError
            ? "rgba(239,68,68,0.4)"
            : isSuccess
            ? "rgba(34,197,94,0.4)"
            : "rgba(99,102,241,0.4)"
        }`,
        color: isError ? "#f87171" : isSuccess ? "#4ade80" : "#a5b4fc",
        fontSize: "13px",
        fontWeight: 500,
        letterSpacing: "0.01em",
      }}
    >
      {STATUS_LABELS[status]}
    </div>
  );
}
