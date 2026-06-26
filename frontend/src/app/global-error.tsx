"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body className="font-sans antialiased" style={{ background: "var(--background)", color: "var(--text-primary)", margin: 0 }}>
        <div style={{ display: "flex", minHeight: "100vh", alignItems: "center", justifyContent: "center", padding: "32px" }}>
          <div
            style={{
              width: "100%",
              maxWidth: "400px",
              border: "1px solid var(--border)",
              borderRadius: "12px",
              background: "var(--surface)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "16px 20px",
                background: "var(--surface-recessed)",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <span
                style={{
                  display: "flex",
                  height: "32px",
                  width: "32px",
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: "8px",
                  background: "var(--surface-ai)",
                  color: "var(--ai-accent)",
                }}
              >
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0" />
                </svg>
              </span>
              <h2 style={{ fontSize: "14px", fontWeight: 600, margin: 0, color: "var(--text-primary)" }}>
                Critical error
              </h2>
            </div>
            <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
              <p style={{ fontSize: "14px", margin: 0, color: "var(--text-secondary)", lineHeight: "20px" }}>
                A critical error occurred. Please try again or contact support if the problem persists.
              </p>
              {error.digest && (
                <p style={{ fontSize: "12px", margin: 0, color: "var(--text-muted)" }}>
                  Error reference: <code style={{ fontFamily: "monospace", color: "var(--text-secondary)" }}>{error.digest}</code>
                </p>
              )}
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <button
                  onClick={() => reset()}
                  style={{
                    display: "inline-flex",
                    height: "32px",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "0 16px",
                    borderRadius: "8px",
                    fontSize: "13px",
                    fontWeight: 500,
                    border: "none",
                    cursor: "pointer",
                    background: "var(--primary)",
                    color: "#fff",
                  }}
                >
                  Try again
                </button>
                <a
                  href="/dashboard"
                  style={{
                    display: "inline-flex",
                    height: "32px",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "0 16px",
                    borderRadius: "8px",
                    fontSize: "13px",
                    fontWeight: 500,
                    textDecoration: "none",
                    color: "var(--text-secondary)",
                  }}
                >
                  Go to Dashboard
                </a>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
