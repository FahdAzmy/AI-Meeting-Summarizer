/**
 * tests/unit/zoom.test.ts
 * -----------------------
 * Unit tests for the Zoom SDK wrapper (src/lib/zoom.ts).
 *
 * The @zoom/meetingsdk package loads a heavy WebAssembly binary and
 * requires a real browser environment. We mock the entire module here
 * so the tests are fast and runnable in jsdom without a real Zoom app.
 */

import {
  parseZoomUrl,
  fetchZoomSignature,
  initZoomClient,
  joinZoomMeeting,
} from "@/lib/zoom";

// ---------------------------------------------------------------------------
// Mock: @zoom/meetingsdk
// ---------------------------------------------------------------------------
// The real SDK uses an options-object pattern where success/error callbacks
// are properties on the argument:
//   ZoomMtg.init({ leaveUrl: "/", success: () => {}, error: () => {} })
//   ZoomMtg.join({ signature, ..., success: () => {}, error: () => {} })
jest.mock("@zoom/meetingsdk", () => ({
  ZoomMtg: {
    setZoomJSLib: jest.fn(),
    preLoadWasm: jest.fn(),
    prepareWebSDK: jest.fn(),
    init: jest.fn((opts: { success?: Function; error?: Function }) => {
      if (opts.success) opts.success();
    }),
    join: jest.fn((opts: { success?: Function; error?: Function }) => {
      if (opts.success) opts.success();
    }),
  },
}));

// ---------------------------------------------------------------------------
// Mock: global fetch (used by fetchZoomSignature)
// ---------------------------------------------------------------------------
global.fetch = jest.fn();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mockFetchResponse(body: object, status = 200) {
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValueOnce(body),
  });
}

// ===========================================================================
// parseZoomUrl
// ===========================================================================

describe("parseZoomUrl", () => {
  it("parses a standard zoom.us/j/{id} URL without passcode", () => {
    const result = parseZoomUrl("https://zoom.us/j/1234567890");
    expect(result).toEqual({ meetingNumber: "1234567890", passcode: "" });
  });

  it("parses a URL with a ?pwd= passcode", () => {
    const result = parseZoomUrl("https://zoom.us/j/1234567890?pwd=abc123");
    expect(result).toEqual({ meetingNumber: "1234567890", passcode: "abc123" });
  });

  it("parses a company-subdomain URL", () => {
    const result = parseZoomUrl("https://acme.zoom.us/j/9876543210?pwd=xyz");
    expect(result).toEqual({ meetingNumber: "9876543210", passcode: "xyz" });
  });

  it("returns null for a non-Zoom URL", () => {
    expect(parseZoomUrl("https://meet.google.com/abc-def")).toBeNull();
  });

  it("returns null for an empty string", () => {
    expect(parseZoomUrl("")).toBeNull();
  });

  it("returns null for a plain-text string", () => {
    expect(parseZoomUrl("not a url")).toBeNull();
  });
});

// ===========================================================================
// fetchZoomSignature
// ===========================================================================

describe("fetchZoomSignature", () => {
  afterEach(() => jest.clearAllMocks());

  it("calls the backend /zoom/signature endpoint", async () => {
    mockFetchResponse({ signature: "jwt.token.here", sdk_key: "my_key" });
    await fetchZoomSignature("1234567890", 0);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/zoom/signature"),
      expect.objectContaining({ method: "POST" })
    );
  });

  it("returns signature and sdk_key from the response", async () => {
    mockFetchResponse({ signature: "jwt.token.here", sdk_key: "my_key" });
    const result = await fetchZoomSignature("1234567890", 0);
    expect(result.signature).toBe("jwt.token.here");
    expect(result.sdk_key).toBe("my_key");
  });

  it("sends meeting_number and role in the POST body", async () => {
    mockFetchResponse({ signature: "jwt.token.here", sdk_key: "my_key" });
    await fetchZoomSignature("9876543210", 1);
    const call = (global.fetch as jest.Mock).mock.calls[0];
    const body = JSON.parse(call[1].body);
    expect(body).toMatchObject({ meeting_number: "9876543210", role: 1 });
  });

  it("throws when the server returns a non-OK status", async () => {
    mockFetchResponse({ detail: "Zoom SDK credentials not configured on the server." }, 500);
    await expect(fetchZoomSignature("1234567890", 0)).rejects.toThrow();
  });
});

// ===========================================================================
// initZoomClient
// ===========================================================================

describe("initZoomClient", () => {
  afterEach(() => jest.clearAllMocks());

  it("calls setZoomJSLib, preLoadWasm, prepareWebSDK, and init", async () => {
    const { ZoomMtg } = await import("@zoom/meetingsdk");
    await initZoomClient("test_sdk_key", "AI Summarizer");
    expect(ZoomMtg.setZoomJSLib).toHaveBeenCalledWith(
      expect.stringContaining("source.zoom.us/3.13.2/lib"),
      "/av"
    );
    expect(ZoomMtg.preLoadWasm).toHaveBeenCalled();
    expect(ZoomMtg.prepareWebSDK).toHaveBeenCalled();
    expect(ZoomMtg.init).toHaveBeenCalledWith(
      expect.objectContaining({
        leaveUrl: "/",
        patchJsMedia: true,
        disablePreview: true,
        success: expect.any(Function),
        error: expect.any(Function),
      })
    );
  });
});

// ===========================================================================
// joinZoomMeeting
// ===========================================================================

describe("joinZoomMeeting", () => {
  afterEach(() => jest.clearAllMocks());

  it("calls ZoomMtg.join with correct parameters", async () => {
    const { ZoomMtg } = await import("@zoom/meetingsdk");
    await joinZoomMeeting({
      signature: "jwt.token",
      sdkKey: "sdk_key",
      meetingNumber: "1234567890",
      passcode: "secret",
      userName: "AI Summarizer",
    });
    expect(ZoomMtg.join).toHaveBeenCalledWith(
      expect.objectContaining({
        signature: "jwt.token",
        sdkKey: "sdk_key",
        meetingNumber: "1234567890",
        passWord: "secret",
        userName: "AI Summarizer",
        success: expect.any(Function),
        error: expect.any(Function),
      })
    );
  });
});
