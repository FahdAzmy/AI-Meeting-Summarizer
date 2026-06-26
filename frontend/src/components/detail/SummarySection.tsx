import React from "react";

interface SummarySectionProps {
  summary: string | null;
}

export function SummarySection({ summary }: SummarySectionProps) {
  if (!summary) return null;

  return (
    <section className="panel overflow-hidden">
      <div className="panel-header flex items-center gap-2.5">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--surface-ai)] text-[var(--ai-accent)]">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m12 3 1.7 5.3H19l-4.3 3.2 1.7 5.3L12 13.6l-4.4 3.2 1.7-5.3L5 8.3h5.3z" />
          </svg>
        </span>
        <h2 className="text-sm font-bold uppercase text-[var(--ai-accent)]">AI Summary</h2>
      </div>
      <div className="p-6">
        <p className="whitespace-pre-wrap break-words text-[15px] leading-7 text-[var(--text-primary)]">{summary}</p>
      </div>
    </section>
  );
}
