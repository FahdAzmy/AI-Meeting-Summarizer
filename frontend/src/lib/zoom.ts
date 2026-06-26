/**
 * src/lib/zoom.ts
 * ---------------
 * Zoom Meeting SDK wrapper for the AI Meeting Summariser.
 *
 * This module encapsulates:
 *  1. URL parsing  — extract meeting ID and passcode from any Zoom URL.
 *  2. Signature fetching — call the backend /api/zoom/signature endpoint.
 *  3. SDK initialisation — configure ZoomMtg before joining.
 *  4. Meeting join — join a Zoom meeting using the SDK.
 *
 * The @zoom/meetingsdk package loads WebAssembly assets from a CDN.
 * All calls are async and return typed results.
 *
 * Usage (from the /zoom-meeting page)
 * ------------------------------------
 *  const details = parseZoomUrl(link);
 *  if (!details) throw new Error("Invalid Zoom URL");
 *
 *  const { signature, sdk_key } = await fetchZoomSignature(details.meetingNumber, 0);
 *  await initZoomClient(sdk_key, "AI Summarizer");
 *  await joinZoomMeeting({ signature, sdkKey: sdk_key, ...details, userName: "AI Summarizer" });
 */

"use client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ZoomUrlDetails {
  meetingNumber: string;
  passcode: string;
}

export interface ZoomSignatureResult {
  signature: string;
  sdk_key: string;
}

export interface JoinMeetingOptions {
  signature: string;
  sdkKey: string;
  meetingNumber: string;
  passcode: string;
  userName: string;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/**
 * Matches zoom.us and company-subdomain Zoom meeting URLs.
 * Groups: (1) meeting ID, (2) passcode (optional).
 */
const ZOOM_URL_REGEX =
  /https?:\/\/(?:[a-z0-9-]+\.)?zoom\.us\/j\/(\d+)(?:\?pwd=([a-zA-Z0-9]+))?/;

/**
 * Backend base URL — reads NEXT_PUBLIC_API_URL or falls back to localhost.
 */
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * The installed @zoom/meetingsdk version.
 * Must match the CDN path used in setZoomJSLib so that the WASM assets
 * are compatible with the JS bundle.
 */
const ZOOM_SDK_VERSION = "3.13.2";

// ---------------------------------------------------------------------------
// 1. URL Parsing
// ---------------------------------------------------------------------------

/**
 * Extract the meeting number and optional passcode from a Zoom URL.
 *
 * @param url  A Zoom meeting URL (zoom.us or company-subdomain).
 * @returns    `ZoomUrlDetails` on success, `null` if the URL is not a Zoom link.
 */
export function parseZoomUrl(url: string): ZoomUrlDetails | null {
  const match = ZOOM_URL_REGEX.exec(url);
  if (!match) return null;

  return {
    meetingNumber: match[1],
    passcode: match[2] ?? "",
  };
}

// ---------------------------------------------------------------------------
// 2. Signature Fetching
// ---------------------------------------------------------------------------

/**
 * Request a short-lived JWT signature from the backend.
 *
 * The backend signs the token with `ZOOM_SDK_CLIENT_SECRET` — the secret
 * never reaches the browser.
 *
 * @param meetingNumber  The numeric Zoom meeting ID (as a string).
 * @param role           0 = attendee, 1 = host.
 * @throws               Error if the network request fails or the server returns
 *                       a non-2xx status.
 */
export async function fetchZoomSignature(
  meetingNumber: string,
  role: 0 | 1
): Promise<ZoomSignatureResult> {
  const response = await fetch(`${API_BASE}/zoom/signature`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ meeting_number: meetingNumber, role }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(
      `Failed to fetch Zoom signature (${response.status}): ${error?.detail ?? "Unknown error"}`
    );
  }

  return response.json() as Promise<ZoomSignatureResult>;
}

// ---------------------------------------------------------------------------
// 3. SDK Initialisation
// ---------------------------------------------------------------------------

/**
 * Initialise the Zoom Meeting SDK client (Client View).
 *
 * Must be called once before `joinZoomMeeting`. The SDK loads WebAssembly
 * assets; allow up to 15 seconds for this to complete.
 *
 * The Client View SDK automatically creates a #zmmtg-root element in the
 * DOM via prepareWebSDK() — the host page must NOT manually render its own
 * #zmmtg-root div.
 *
 * @param sdkKey   The `ZOOM_SDK_CLIENT_ID` returned by the backend.
 * @param userName The display name shown in the meeting (e.g. "AI Summarizer").
 */
export async function initZoomClient(
  sdkKey: string,
  userName: string
): Promise<void> {
  const { ZoomMtg } = await import("@zoom/meetingsdk");

  // Point the SDK at Zoom's CDN for WASM assets.
  // CRITICAL: The version MUST match the installed npm package version,
  // otherwise the WASM binaries won't be compatible with the JS bundle
  // and the SDK will fail silently or throw cryptic errors.
  ZoomMtg.setZoomJSLib(`https://source.zoom.us/${ZOOM_SDK_VERSION}/lib`, "/av");

  console.info("[zoom.ts] preLoadWasm…");
  ZoomMtg.preLoadWasm();

  console.info("[zoom.ts] prepareWebSDK…");
  ZoomMtg.prepareWebSDK();

  console.info("[zoom.ts] Calling ZoomMtg.init…");

  return new Promise<void>((resolve, reject) => {
    ZoomMtg.init({
      leaveUrl: "/",           // Redirect target after leaving
      debug: true,             // Enable debug logging in console
      patchJsMedia: true,      // Auto-apply latest media dependency fix
      disablePreview: true,    // Skip audio/video preview for bot usage
      success: () => {
        console.info("[zoom.ts] ZoomMtg.init succeeded");
        resolve();
      },
      error: (err: unknown) => {
        console.error("[zoom.ts] ZoomMtg.init failed:", err);
        reject(err);
      },
    });
  });
}

// ---------------------------------------------------------------------------
// 4. Meeting Join
// ---------------------------------------------------------------------------

/**
 * Join a Zoom meeting using the initialised SDK client.
 *
 * Resolves when the SDK confirms the join; rejects on failure.
 *
 * @param options  Join parameters including signature, sdkKey, meetingNumber,
 *                 passcode, and userName.
 */
export async function joinZoomMeeting(options: JoinMeetingOptions): Promise<void> {
  const { ZoomMtg } = await import("@zoom/meetingsdk");

  console.info("[zoom.ts] Calling ZoomMtg.join with meetingNumber:", options.meetingNumber);

  return new Promise<void>((resolve, reject) => {
    ZoomMtg.join({
      signature: options.signature,
      sdkKey: options.sdkKey,
      meetingNumber: options.meetingNumber,
      passWord: options.passcode,
      userName: options.userName,
      userEmail: "",           // Optional — leave empty for anonymous join
      success: (res: unknown) => {
        console.info("[zoom.ts] ZoomMtg.join succeeded:", res);
        resolve();
      },
      error: (err: unknown) => {
        console.error("[zoom.ts] ZoomMtg.join failed:", err);
        reject(err);
      },
    });
  });
}
