"use client";

import { useEffect, useRef } from "react";

interface HelpDrawerProps {
  open: boolean;
  onClose: () => void;
}

const shortcuts = [
  { keys: ["Alt", "N"], label: "New meeting" },
  { keys: ["Ctrl", "K"], label: "Command palette" },
  { keys: ["Ctrl", "E"], label: "Export summary" },
  { keys: ["Escape"], label: "Close drawer / cancel" },
];

const glossary = [
  { term: "Pipeline", definition: "The end-toend process: join → record → transcribe → summarize → deliver." },
  { term: "STT Engine", definition: "Speech-to-text engine used for transcription (e.g. Deepgram, Whisper)." },
  { term: "Status", definition: "Current stage of a meeting pipeline: pending, recording, transcribing, summarizing, delivered, failed." },
  { term: "Deliverable", definition: "Final output pushed to the configured storage destination (email, Slack, Notion)." },
];

const faq = [
  { q: "How do I start a meeting?", a: "Go to Dashboard → paste a meeting link → configure options → click Start." },
  { q: "Where are past meetings?", a: "Open the History tab. You can search, filter by platform, or re-export any past session." },
  { q: "What storage options are supported?", a: "Email, Slack, and Notion. Configure in Settings → Storage." },
  { q: "Can I change the transcription engine?", a: "Yes. Go to Settings → Speech-to-Text and choose between Deepgram, Whisper, or AssemblyAI." },
];

export function HelpDrawer({ open, onClose }: HelpDrawerProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  useEffect(() => {
    if (open) {
      const panel = panelRef.current;
      if (panel) {
        const firstLink = panel.querySelector<HTMLButtonElement>("button");
        firstLink?.focus();
      }
    }
  }, [open]);

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/20"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <div
        ref={panelRef}
        role="dialog"
        aria-label="Help and documentation"
        aria-modal="true"
        className={`fixed left-0 top-0 z-50 h-full w-[min(360px,100vw)] overflow-y-auto border-r border-[var(--border)] bg-[var(--surface)] shadow-xl transition-transform duration-200 md:left-[220px] ${
          open ? "translate-x-0" : "pointer-events-none -translate-x-full md:-translate-x-[calc(100%+220px)]"
        }`}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface-recessed)] px-5 py-3">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Help &amp; documentation</h2>
          <button
            onClick={onClose}
            aria-label="Close help drawer"
            className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-low)] hover:text-[var(--text-primary)]"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-8 p-5">
          {/* Keyboard shortcuts */}
          <section>
            <h3 className="label-caps mb-3">Keyboard shortcuts</h3>
            <ul className="space-y-2">
              {shortcuts.map((s) => (
                <li key={s.keys[0]} className="flex items-center justify-between text-sm">
                  <span className="text-[var(--text-secondary)]">{s.label}</span>
                  <span className="flex items-center gap-1">
                    {s.keys.map((k) => (
                      <kbd
                        key={k}
                        className="inline-flex min-w-[24px] items-center justify-center rounded-md border border-[var(--border)] bg-[var(--surface-recessed)] px-1.5 py-0.5 text-[11px] font-medium text-[var(--text-secondary)]"
                      >
                        {k}
                      </kbd>
                    ))}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          {/* Glossary */}
          <section>
            <h3 className="label-caps mb-3">Glossary</h3>
            <dl className="space-y-3">
              {glossary.map((g) => (
                <div key={g.term}>
                  <dt className="text-sm font-medium text-[var(--text-primary)]">{g.term}</dt>
                  <dd className="mt-0.5 text-sm text-[var(--text-secondary)]">{g.definition}</dd>
                </div>
              ))}
            </dl>
          </section>

          {/* FAQ */}
          <section>
            <h3 className="label-caps mb-3">Frequently asked questions</h3>
            <div className="space-y-4">
              {faq.map((f, i) => (
                <div key={i}>
                  <p className="text-sm font-medium text-[var(--text-primary)]">Q: {f.q}</p>
                  <p className="mt-0.5 text-sm text-[var(--text-secondary)]">A: {f.a}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
