"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Meeting } from "@/lib/types";
import { MeetingsTable } from "@/components/history/MeetingsTable";
import { useToast } from "@/components/ui/Toast";
import Link from "next/link";

const StatCard = ({
  label, value, icon, color
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}) => (
  <div className="bg-white rounded-2xl border border-stone-200 shadow-sm px-5 py-4 flex items-start gap-4">
    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
      {icon}
    </div>
    <div>
      <p className="text-xs font-semibold text-stone-400 uppercase tracking-wider">{label}</p>
      <p className="mt-1 text-2xl font-heading font-bold text-stone-900 leading-none">{value}</p>
    </div>
  </div>
);

export default function HistoryPage() {
  const [meetings, setMeetings] = useState<Partial<Meeting>[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
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
    return () => { isMounted = false; };
  }, [showToast]);

  const completed = meetings.filter(m => m.status === "completed").length;
  const avgDuration = (() => {
    const withDur = meetings.filter(m => m.duration_minutes);
    if (!withDur.length) return "—";
    const avg = withDur.reduce((s, m) => s + (m.duration_minutes ?? 0), 0) / withDur.length;
    return `${Math.round(avg)} min`;
  })();

  const filtered = meetings.filter(m =>
    !search ||
    m.meeting_link?.toLowerCase().includes(search.toLowerCase()) ||
    m.platform?.toLowerCase().includes(search.toLowerCase()) ||
    m.status?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="px-8 py-8 space-y-7 animate-fade-up">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold text-stone-400 uppercase tracking-widest mb-1">Workspace</p>
          <h1 className="font-heading text-2xl font-bold text-stone-900">Meeting History</h1>
          <p className="mt-1 text-sm text-stone-500">All recorded and processed meeting sessions.</p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-stone-900 text-white text-sm font-semibold hover:bg-stone-800 transition-colors shadow-sm shadow-stone-900/10 active:scale-[0.97] shrink-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New session
        </Link>
      </div>

      {/* Stats */}
      {!isLoading && meetings.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 animate-fade-up animation-delay-100">
          <StatCard
            label="Total sessions"
            value={meetings.length}
            color="bg-stone-100"
            icon={
              <svg className="w-4 h-4 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            }
          />
          <StatCard
            label="Completed"
            value={completed}
            color="bg-emerald-50"
            icon={
              <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <StatCard
            label="Avg. duration"
            value={avgDuration}
            color="bg-blue-50"
            icon={
              <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>
      )}

      {/* Search bar + table */}
      <div className="space-y-3 animate-fade-up animation-delay-200">
        {meetings.length > 0 && (
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-xs">
              <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg className="w-4 h-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                placeholder="Filter meetings..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full h-9 pl-9 pr-4 text-sm border border-stone-200 rounded-xl bg-white placeholder:text-stone-400 text-stone-900 focus:outline-none focus:ring-2 focus:ring-stone-900/10 focus:border-stone-400 transition-all"
              />
            </div>
            <span className="text-xs text-stone-400 font-medium">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
          </div>
        )}

        {isLoading ? (
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm">
            <div className="px-6 py-14 text-center">
              <div className="inline-flex items-center gap-3 text-sm text-stone-400">
                <div className="w-4 h-4 rounded-full border-2 border-stone-300 border-t-stone-700 animate-spin" />
                Loading your sessions...
              </div>
            </div>
          </div>
        ) : meetings.length === 0 ? (
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm">
            <div className="px-6 py-16 text-center">
              <div className="w-14 h-14 rounded-2xl bg-stone-100 flex items-center justify-center mx-auto mb-5">
                <svg className="w-7 h-7 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-heading font-semibold text-base text-stone-900">No sessions yet</h3>
              <p className="text-sm text-stone-400 mt-1.5 mb-5 max-w-xs mx-auto">
                Start your first AI-assisted meeting on the dashboard.
              </p>
              <Link
                href="/"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-stone-900 text-white text-sm font-semibold hover:bg-stone-800 transition-colors"
              >
                Go to Dashboard
              </Link>
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm px-6 py-10 text-center text-sm text-stone-400">
            No meetings match &quot;{search}&quot;.
          </div>
        ) : (
          <MeetingsTable meetings={filtered} />
        )}
      </div>
    </div>
  );
}
