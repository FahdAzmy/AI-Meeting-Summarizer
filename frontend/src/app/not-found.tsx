import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--background)]">
      <div className="panel max-w-sm">
        <div className="panel-header flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--surface-ai)] text-[var(--ai-accent)]">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.9 9.9a3 3 0 1 1 4.2 4.2L12 16l-.5-2.5A2 2 0 0 0 10.5 12H9a3 3 0 0 1 .9-2.1" />
              <circle cx="12" cy="12" r="10" />
            </svg>
          </span>
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Page not found</h2>
        </div>
        <div className="space-y-4 p-6">
          <p className="text-sm text-[var(--text-secondary)]">
            The page you are looking for does not exist or has been moved.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex h-8 items-center justify-center gap-2 rounded-lg bg-[var(--primary)] px-4 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)]"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
