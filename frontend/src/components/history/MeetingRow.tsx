import React from "react";
import Link from "next/link";
import { Meeting } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";
import { PlatformBadge } from "../dashboard/PlatformBadge";

interface MeetingRowProps {
  meeting: Partial<Meeting>;
  isEven?: boolean;
}

export function MeetingRow({ meeting, isEven }: MeetingRowProps) {
  const date = meeting.date
    ? new Date(meeting.date).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null;

  const time = meeting.date
    ? new Date(meeting.date).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <tr className={`group border-b border-[var(--border)] transition-colors hover:bg-[rgb(245_158_11_/_0.06)] ${isEven ? "bg-[var(--surface)]" : "bg-[var(--surface-low)]"}`}>
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--surface-recessed)] text-sm font-semibold text-[var(--text-secondary)]">
            {meeting.date ? new Date(meeting.date).getDate() : "--"}
          </div>
          <div>
            <div className="text-sm font-medium text-[var(--text-primary)]">{date || "--"}</div>
            {time && <div className="mt-0.5 text-xs text-[var(--text-muted)]">{time}</div>}
          </div>
        </div>
      </td>
      <td className="px-6 py-4">
        {meeting.platform ? <PlatformBadge platform={meeting.platform} /> : <span className="text-sm text-[var(--text-muted)]">--</span>}
      </td>
      <td className="px-6 py-4">
        {meeting.duration_minutes ? (
          <span className="chip">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 2m6-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0" />
            </svg>
            {meeting.duration_minutes}m
          </span>
        ) : (
          <span className="text-sm text-[var(--text-muted)]">--</span>
        )}
      </td>
      <td className="px-6 py-4">
        <StatusBadge status={meeting.status || "pending"} />
      </td>
      <td className="px-6 py-4 text-right">
        <Link
          href={`/history/${meeting.id}`}
          className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold text-[var(--primary)] transition-colors hover:bg-[rgb(245_158_11_/_0.1)]"
        >
          View
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m9 5 7 7-7 7" />
          </svg>
        </Link>
      </td>
    </tr>
  );
}
