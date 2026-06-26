"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Meeting } from "@/lib/types";
import { MeetingsTable } from "@/components/history/MeetingsTable";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";

export default function HistoryPage() {
  const [meetings, setMeetings] = useState<Partial<Meeting>[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [platform, setPlatform] = useState("all");
  const [isExporting, setIsExporting] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    let isMounted = true;
    const fetchMeetings = async () => {
      try {
        setIsLoading(true);
        const data = await api.getMeetings();
        if (isMounted) setMeetings(data);
      } catch (error) {
        console.error(error);
        if (isMounted) showToast("Failed to fetch meeting history.", "error");
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    fetchMeetings();
    return () => {
      isMounted = false;
    };
  }, [showToast]);

  const completed = meetings.filter((meeting) => meeting.status === "completed").length;

  const handleExportAll = async () => {
    setIsExporting(true);
    try {
      await api.exportAllMeetingsExcel();
      showToast("Export downloaded successfully.", "success");
    } catch (error) {
      console.error(error);
      showToast(error instanceof Error ? error.message : "Failed to export meetings.", "error");
    } finally {
      setIsExporting(false);
    }
  };

  const avgDuration = useMemo(() => {
    const withDuration = meetings.filter((meeting) => meeting.duration_minutes);
    if (!withDuration.length) return "--";
    const avg = withDuration.reduce((sum, meeting) => sum + (meeting.duration_minutes ?? 0), 0) / withDuration.length;
    return `${Math.round(avg)} min`;
  }, [meetings]);

  const platforms = useMemo(
    () => Array.from(new Set(meetings.map((meeting) => meeting.platform).filter(Boolean))).sort() as string[],
    [meetings],
  );

  const filtered = meetings.filter((meeting) => {
    const query = search.toLowerCase();
    const matchesSearch =
      !query ||
      meeting.title?.toLowerCase().includes(query) ||
      meeting.meeting_link?.toLowerCase().includes(query) ||
      meeting.platform?.toLowerCase().includes(query) ||
      meeting.status?.toLowerCase().includes(query);
    const matchesPlatform = platform === "all" || meeting.platform === platform;
    return matchesSearch && matchesPlatform;
  });

  return (
    <div className="page-canvas animate-fade-up">
      <div className="space-y-6">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <h1 className="text-3xl font-bold text-[var(--text-primary)]">History</h1>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              {isLoading ? "Loading meetings..." : `${meetings.length} meetings`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {completed > 0 && (
              <Button type="button" variant="outline" onClick={handleExportAll} disabled={isExporting}>
                {isExporting ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--primary)]" />
                ) : (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v12m0 0 4-4m-4 4-4-4M5 21h14" />
                  </svg>
                )}
                {isExporting ? "Exporting" : "Export CSV"}
              </Button>
            )}
            <Link href="/dashboard">
              <Button type="button">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14M5 12h14" />
                </svg>
                New Session
              </Button>
            </Link>
          </div>
        </div>

        {!isLoading && meetings.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="panel p-5">
              <p className="label-caps">Total</p>
              <p className="mt-3 text-2xl font-bold text-[var(--text-primary)]">{meetings.length}</p>
            </div>
            <div className="panel p-5">
              <p className="label-caps">Completed</p>
              <p className="mt-3 text-2xl font-bold text-[var(--primary)]">{completed}</p>
            </div>
            <div className="panel p-5">
              <p className="label-caps">Avg. Duration</p>
              <p className="mt-3 text-2xl font-bold text-[var(--primary)]">{avgDuration}</p>
            </div>
          </div>
        )}

        {meetings.length > 0 && (
          <div className="panel flex flex-wrap items-center gap-4 p-3">
            <div className="relative w-full sm:w-[280px]">
              <svg className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-4.3-4.3m1.3-5.2a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0" />
              </svg>
              <input
                type="text"
                aria-label="Search sessions"
                placeholder="Search titles, attendees..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                maxLength={200}
                className="focus-ring h-9 w-full rounded-lg border border-transparent bg-[var(--surface-recessed)] pl-10 pr-4 text-sm text-[var(--text-primary)] transition-colors focus:bg-[var(--surface)]"
              />
            </div>
            <div className="relative">
              <select
                aria-label="Filter by platform"
                value={platform}
                onChange={(event) => setPlatform(event.target.value)}
                className="focus-ring h-9 cursor-pointer appearance-none rounded-lg border border-transparent bg-[var(--surface-recessed)] py-2 pl-4 pr-10 text-sm text-[var(--text-primary)] transition-colors focus:bg-[var(--surface)]"
              >
                <option value="all">All Platforms</option>
                {platforms.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
              <svg className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m6 9 6 6 6-6" />
              </svg>
            </div>
            <span aria-live="polite" className="text-xs font-medium text-[var(--text-muted)]">
              {filtered.length} result{filtered.length !== 1 ? "s" : ""}
            </span>
          </div>
        )}

        {isLoading ? (
          <div className="panel px-6 py-20 text-center">
            <div className="inline-flex items-center gap-3">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--primary)]" />
              <span className="text-sm text-[var(--text-secondary)]">Loading sessions...</span>
            </div>
          </div>
        ) : meetings.length === 0 ? (
          <div className="panel px-6 py-20 text-center">
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--surface-recessed)] text-[var(--text-muted)]">
              <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3M5 11h14M5 21h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2" />
              </svg>
            </div>
            <h3 className="text-base font-semibold text-[var(--text-primary)]">No sessions yet</h3>
            <p className="mx-auto mt-2 max-w-xs text-sm text-[var(--text-secondary)]">
              Record your first AI-assisted meeting to start building a searchable workspace history.
            </p>
            <Link href="/dashboard" className="mt-6 inline-flex">
              <Button type="button">Start Recording</Button>
            </Link>
          </div>
        ) : filtered.length === 0 ? (
          <div className="panel px-6 py-12 text-center text-sm text-[var(--text-secondary)]">
            No meetings match "{search}".
          </div>
        ) : (
          <MeetingsTable meetings={filtered} />
        )}
      </div>
    </div>
  );
}
