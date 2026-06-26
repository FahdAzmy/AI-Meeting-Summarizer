"use client";

import React, { useState } from "react";
import { Button } from "../ui/Button";

interface TranscriptViewerProps {
  transcript: string | null;
}

export function TranscriptViewer({ transcript }: TranscriptViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!transcript) return null;

  const lines = transcript.split("\n").filter((line) => line.trim());

  return (
    <section className="panel overflow-hidden">
      <div className="panel-header flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--surface)] text-[var(--text-secondary)] ring-1 ring-[var(--border)]">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h7M7 16h10M5 3h14a2 2 0 0 1 2 2v14l-4-3H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2" />
            </svg>
          </span>
          <div>
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">Transcript</h2>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">{lines.length} lines</p>
          </div>
        </div>
        <Button type="button" variant="outline" onClick={() => setIsExpanded((current) => !current)}>
          <svg className={`h-4 w-4 transition-transform ${isExpanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m6 9 6 6 6-6" />
          </svg>
          {isExpanded ? "Collapse" : "Expand"}
        </Button>
      </div>

      {isExpanded && (
        <div className="p-5">
          <div className="max-h-80 overflow-y-auto rounded-lg border border-[var(--border)] bg-[var(--surface-recessed)]">
            <div className="p-4 font-mono text-sm leading-6 text-[var(--text-primary)]">
              {lines.map((line, index) => (
                <div key={`${line}-${index}`} className="border-b border-[var(--border)] py-2 last:border-0">
                  {line}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
