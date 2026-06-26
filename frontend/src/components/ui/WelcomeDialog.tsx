"use client";

import { useEffect, useState } from "react";

const ONBOARDING_KEY = "meetingai_onboarding_done";

const steps = [
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.8 10.2a4 4 0 0 0-5.6 0l-4 4a4 4 0 0 0 5.6 5.6l1.1-1.1" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.2 13.8a4 4 0 0 0 5.6 0l4-4a4 4 0 0 0-5.6-5.6l-1.1 1.1" />
      </svg>
    ),
    title: "Paste a meeting link",
    description: "Start from any Google Meet, Zoom, or Teams link. Assign teams or members so the summary routes to the right people.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.5 11.5 15 15 9.5" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18" />
      </svg>
    ),
    title: "Let the pipeline run",
    description: "The bot joins, records, transcribes, and summarises — every stage visible in the status panel. No manual steps.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.3v-2.8a7.5 7.5 0 0 0-15 0v2.8" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a3 3 0 0 0 3-3H9a3 3 0 0 0 3 3" />
      </svg>
    ),
    title: "Get structured records",
    description: "Transcripts, summaries, action items, and decisions land in your history — searchable, exportable, shareable.",
  },
];

export function WelcomeDialog() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const done = localStorage.getItem(ONBOARDING_KEY);
    if (done !== "true") {
      setOpen(true);
    }
  }, []);

  const dismiss = () => {
    localStorage.setItem(ONBOARDING_KEY, "true");
    setOpen(false);
  };

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm" onClick={dismiss} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Welcome to MeetingAI"
        className="fixed left-1/2 top-1/2 z-50 w-[440px] max-w-[calc(100vw-32px)] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-2xl"
      >
        <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
          <div className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--primary)] text-white">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.1-7.5 12-7.5 12s-7.5-4.9-7.5-12a7.5 7.5 0 1 1 15 0" />
              </svg>
            </span>
            <span className="text-sm font-semibold text-[var(--text-primary)]">Welcome to MeetingAI</span>
          </div>
          <span className="text-xs text-[var(--text-muted)]">{step + 1} of {steps.length}</span>
        </div>

        <div className="px-6 py-8">
          <div className="flex flex-col items-center text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--primary-soft)] text-[var(--primary)]">
              {steps[step].icon}
            </span>
            <h2 className="mt-4 text-lg font-bold text-[var(--text-primary)]">{steps[step].title}</h2>
            <p className="mt-2 max-w-sm text-sm leading-6 text-[var(--text-secondary)]">{steps[step].description}</p>
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-[var(--border)] bg-[var(--surface-recessed)] px-6 py-4">
          <button
            onClick={dismiss}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-low)]"
          >
            Skip
          </button>
          <div className="flex items-center gap-2">
            {step > 0 && (
              <button
                onClick={() => setStep((s) => s - 1)}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-1.5 text-xs font-medium text-[var(--text-primary)] transition-colors hover:bg-[var(--surface-low)]"
              >
                Back
              </button>
            )}
            {step < steps.length - 1 ? (
              <button
                onClick={() => setStep((s) => s + 1)}
                className="rounded-lg bg-[var(--primary)] px-4 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[var(--primary-hover)]"
              >
                Next
              </button>
            ) : (
              <button
                onClick={dismiss}
                className="rounded-lg bg-[var(--primary)] px-4 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[var(--primary-hover)]"
              >
                Got it
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
