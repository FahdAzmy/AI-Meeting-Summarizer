import React from "react";
import { STTProvider } from "@/lib/types";

interface STTSelectorProps {
  value: STTProvider;
  onChange: (value: STTProvider) => void;
}

const providers: Array<{ value: STTProvider; label: string; description: string; badge?: string }> = [
  {
    value: "whisper",
    label: "Whisper API",
    description: "Strong accuracy across accents and multilingual meetings.",
    badge: "Best Accuracy",
  },
  {
    value: "deepgram",
    label: "Deepgram",
    description: "Fast streaming-friendly transcripts for long meetings.",
  },
  {
    value: "assemblyai",
    label: "AssemblyAI",
    description: "Balanced transcript quality with topic detection support.",
  },
];

export function STTSelector({ value, onChange }: STTSelectorProps) {
  return (
    <div className="space-y-3">
      {providers.map((provider) => {
        const isSelected = value === provider.value;
        return (
          <label
            key={provider.value}
            className={`relative flex cursor-pointer items-start gap-4 rounded-lg border p-4 transition-colors ${
              isSelected ? "border-[var(--primary)] bg-[rgb(245_158_11_/_0.08)]" : "border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-low)]"
            }`}
          >
            <input
              type="radio"
              name="stt_provider"
              value={provider.value}
              checked={isSelected}
              onChange={() => onChange(provider.value)}
              className="mt-1 h-4 w-4 text-[var(--primary)] focus:ring-[var(--primary)]"
            />
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-semibold text-[var(--text-primary)]">{provider.label}</span>
                {provider.badge && (
                  <span className="rounded-full border border-[rgb(217_119_6_/_0.30)] bg-[var(--surface-ai)] px-2 py-0.5 text-[10px] font-medium text-[var(--ai-accent)]">
                    {provider.badge}
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs text-[var(--text-secondary)]">{provider.description}</p>
            </div>
          </label>
        );
      })}
    </div>
  );
}
