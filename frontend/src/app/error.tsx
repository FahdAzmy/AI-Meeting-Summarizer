"use client";

import Link from "next/link";
import { useEffect } from "react";
import { Button } from "@/components/ui/Button";

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
    <div className="flex h-screen items-center justify-center bg-[var(--background)]">
      <div className="panel max-w-sm">
        <div className="panel-header flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--surface-ai)] text-[var(--ai-accent)]">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0" />
            </svg>
          </span>
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Something went wrong</h2>
        </div>
        <div className="space-y-4 p-6">
          <p className="text-sm text-[var(--text-secondary)]">
            We encountered an unexpected error. Please try again, or go back to the dashboard.
          </p>
          {error.digest && (
            <p className="text-xs text-[var(--text-muted)]">
              Error reference: <code className="font-mono text-[var(--text-secondary)]">{error.digest}</code>
            </p>
          )}
          <div className="flex items-center gap-3">
            <Button onClick={() => reset()}>Try again</Button>
            <Link
              href="/dashboard"
              className="rounded-lg px-4 py-2 text-xs font-semibold text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-low)]"
            >
              Go to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
