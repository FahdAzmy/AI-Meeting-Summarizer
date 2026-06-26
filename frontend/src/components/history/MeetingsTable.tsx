import React, { useMemo, useState } from "react";
import { Meeting } from "@/lib/types";
import { MeetingRow } from "./MeetingRow";

interface MeetingsTableProps {
  meetings: Partial<Meeting>[];
}

type SortKey = "date" | "platform" | "duration_minutes" | "status";

const headers: { key: SortKey; label: string }[] = [
  { key: "date", label: "Date" },
  { key: "platform", label: "Platform" },
  { key: "duration_minutes", label: "Duration" },
  { key: "status", label: "Status" },
];

function SortIcon({ desc }: { desc: boolean }) {
  return (
    <svg className={`h-3 w-3 ${desc ? "" : "rotate-180"}`} fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={1.7}>
      <path d="M6 2v8m0 0L3 7m3 3 3-3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function MeetingsTable({ meetings }: MeetingsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDesc, setSortDesc] = useState(true);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDesc(!sortDesc);
    else {
      setSortKey(key);
      setSortDesc(true);
    }
  };

  const sorted = useMemo(
    () =>
      [...meetings].sort((a, b) => {
        const aVal = a[sortKey] ?? "";
        const bVal = b[sortKey] ?? "";
        if (aVal < bVal) return sortDesc ? 1 : -1;
        if (aVal > bVal) return sortDesc ? -1 : 1;
        return 0;
      }),
    [meetings, sortKey, sortDesc],
  );

  return (
    <div className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] bg-[var(--surface-recessed)]">
              {headers.map(({ key, label }) => (
                <th
                  key={key}
                  onClick={() => handleSort(key)}
                  className="group cursor-pointer select-none px-6 py-3 text-left text-[11px] font-bold uppercase text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
                >
                  <span className="flex items-center gap-1">
                    {label}
                    <span className={`text-[var(--text-muted)] transition-opacity ${sortKey === key ? "opacity-100" : "opacity-0 group-hover:opacity-50"}`}>
                      <SortIcon desc={sortDesc} />
                    </span>
                  </span>
                </th>
              ))}
              <th className="px-6 py-3 text-right text-[11px] font-bold uppercase text-[var(--text-secondary)]">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((meeting, index) => (
              <MeetingRow key={meeting.id || index} meeting={meeting} isEven={index % 2 === 0} />
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-[var(--border)] bg-[var(--surface-recessed)] px-6 py-3 text-xs font-medium text-[var(--text-muted)]">
        <span>{sorted.length} session{sorted.length !== 1 ? "s" : ""}</span>
        <span>Click row to view details</span>
      </div>
    </div>
  );
}
