"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";

interface Command {
  id: string;
  label: string;
  description: string;
  action: () => void;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");

  const commands: Command[] = [
    { id: "new-meeting", label: "New meeting", description: "Start a new meeting pipeline", action: () => { router.push("/dashboard"); onClose(); } },
    { id: "history", label: "View history", description: "Browse past meetings", action: () => { router.push("/history"); onClose(); } },
    { id: "teams", label: "Manage teams", description: "View and edit teams", action: () => { router.push("/teams"); onClose(); } },
    { id: "settings", label: "Settings", description: "Configure account and integrations", action: () => { router.push("/settings"); onClose(); } },
    { id: "export", label: "Export summary", description: "Export current meeting summary", action: () => { onClose(); } },
  ];

  const filtered = query.trim()
    ? commands.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()) || c.description.toLowerCase().includes(query.toLowerCase()))
    : commands;

  const [selectedIndex, setSelectedIndex] = useState(0);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter" && filtered[selectedIndex]) {
        e.preventDefault();
        filtered[selectedIndex].action();
      } else if (e.key === "Escape") {
        onClose();
      }
    },
    [filtered, selectedIndex, onClose]
  );

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        className={`fixed left-1/2 top-[15%] z-50 w-[480px] max-w-[calc(100vw-32px)] -translate-x-1/2 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-2xl transition-all duration-150 ${
          open ? "scale-100 opacity-100" : "pointer-events-none scale-95 opacity-0"
        }`}
        onKeyDown={handleKeyDown}
      >
        <div className="flex items-center gap-3 border-b border-[var(--border)] px-4 py-3">
          <svg className="h-4 w-4 shrink-0 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-4.3-4.3M17 11a6 6 0 1 0-12 0 6 6 0 0 0 12 0" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            placeholder="Search commands…"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
            className="flex-1 bg-transparent text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-muted)]"
          />
          <kbd className="rounded-md border border-[var(--border)] bg-[var(--surface-recessed)] px-1.5 py-0.5 text-[11px] font-medium text-[var(--text-muted)]">
            ESC
          </kbd>
        </div>

        <div className="max-h-[280px] overflow-y-auto p-2">
          {filtered.length === 0 && (
            <p className="px-3 py-8 text-center text-sm text-[var(--text-muted)]">No commands found</p>
          )}
          {filtered.map((cmd, i) => (
            <button
              key={cmd.id}
              onClick={cmd.action}
              onMouseEnter={() => setSelectedIndex(i)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                i === selectedIndex
                  ? "bg-[var(--primary-soft)] text-[var(--primary)]"
                  : "text-[var(--text-primary)] hover:bg-[var(--surface-low)]"
              }`}
            >
              <span className="flex-1 font-medium">{cmd.label}</span>
              <span className="text-xs text-[var(--text-muted)]">{cmd.description}</span>
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
