import React from "react";
import { StorageBackend } from "@/lib/types";

interface StorageToggleProps {
  value: StorageBackend;
  onChange: (value: StorageBackend) => void;
}

export function StorageToggle({ value, onChange }: StorageToggleProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-[var(--text-primary)]">Transcription Storage</p>
      <p className="text-xs text-[var(--text-secondary)]">Store transcripts and AI outputs in the internal database.</p>
      <label className="flex cursor-pointer items-center gap-4 rounded-lg border-2 border-[var(--primary)] bg-[rgb(245_158_11_/_0.08)] p-4">
        <input
          type="radio"
          name="storage"
          value="database"
          checked={value === "database"}
          onChange={() => onChange("database")}
          className="h-4 w-4 text-[var(--primary)] focus:ring-[var(--primary)]"
        />
        <div>
          <span className="text-sm font-semibold text-[var(--text-primary)]">Database</span>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Best for searchable meeting history and exports.</p>
        </div>
      </label>
    </div>
  );
}
