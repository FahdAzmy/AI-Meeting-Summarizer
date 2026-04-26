"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Meeting } from "@/lib/types";
import { MeetingsTable } from "@/components/history/MeetingsTable";
import { useToast } from "@/components/ui/Toast";
import Link from "next/link";

export default function HistoryPage() {
  const [meetings, setMeetings] = useState<Partial<Meeting>[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
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
    return () => { isMounted = false; };
  }, [showToast]);

  const completed = meetings.filter(m => m.status === "completed").length;

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
    <div className="min-h-screen bg-stone-50 px-4 sm:px-8 py-8 animate-fade-up">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1.5 h-8 bg-gradient-to-b from-emerald-500 to-teal-600 rounded-full" />
              <div>
                <p className="text-[11px] font-bold text-stone-400 uppercase tracking-[0.2em]">Workspace</p>
                <h1 className="text-3xl font-bold text-stone-900 tracking-tight">
                  Meeting History
                </h1>
              </div>
            </div>
            <p className="text-stone-500 ml-5">Your recorded meeting sessions</p>
          </div>
          <div className="flex items-center gap-2">
            {completed > 0 && (
              <button
                onClick={handleExportAll}
                disabled={isExporting}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 transition-all shadow-lg shadow-emerald-600/15 active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isExporting ? (
                  <div className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
                {isExporting ? "Exporting..." : "Export All"}
              </button>
            )}
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-stone-900 text-white text-sm font-semibold hover:bg-stone-800 transition-all shadow-lg shadow-stone-900/15 active:scale-[0.97]"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Session
            </Link>
          </div>
        </div>

        {!isLoading && meetings.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="group bg-white rounded-2xl border border-stone-100 p-5 shadow-sm hover:shadow-md hover:border-stone-200 transition-all">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-stone-100 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-5 h-5 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-semibold text-stone-400 uppercase tracking-wider">Total</p>
                  <p className="text-2xl font-bold text-stone-900">{meetings.length}</p>
                </div>
              </div>
            </div>
            <div className="group bg-white rounded-2xl border border-stone-100 p-5 shadow-sm hover:shadow-md hover:border-stone-200 transition-all">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-semibold text-stone-400 uppercase tracking-wider">Completed</p>
                  <p className="text-2xl font-bold text-emerald-600">{completed}</p>
                </div>
              </div>
            </div>
            <div className="group bg-white rounded-2xl border border-stone-100 p-5 shadow-sm hover:shadow-md hover:border-stone-200 transition-all">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-semibold text-stone-400 uppercase tracking-wider">Avg. Duration</p>
                  <p className="text-2xl font-bold text-blue-600">{avgDuration}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {meetings.length > 0 && (
            <div className="flex items-center gap-3">
              <div className="relative flex-1 max-w-xs">
                <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none">
                  <svg className="w-4 h-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder="Search meetings..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full h-10 pl-10 pr-4 text-sm border border-stone-200 rounded-xl bg-white placeholder:text-stone-400 text-stone-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-400 transition-all"
                />
              </div>
              <span className="text-xs text-stone-400 font-medium px-2">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
            </div>
          )}

          {isLoading ? (
            <div className="bg-white border border-stone-100 rounded-2xl shadow-sm">
              <div className="px-6 py-20 text-center">
                <div className="inline-flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full border-2 border-stone-200 border-t-emerald-600 animate-spin" />
                  <span className="text-stone-500">Loading sessions...</span>
                </div>
              </div>
            </div>
          ) : meetings.length === 0 ? (
            <div className="bg-white border border-stone-100 rounded-2xl shadow-sm">
              <div className="px-6 py-20 text-center">
                <div className="w-16 h-16 rounded-2xl bg-stone-100 flex items-center justify-center mx-auto mb-5">
                  <svg className="w-8 h-8 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-stone-900 mb-2">No sessions yet</h3>
                <p className="text-stone-500 mb-6 max-w-xs mx-auto">
                  Record your first AI-assisted meeting to get started.
                </p>
                <Link
                  href="/"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition-all shadow-lg shadow-emerald-600/15"
                >
                  Start Recording
                </Link>
              </div>
            </div>
          ) : filtered.length === 0 ? (
            <div className="bg-white border border-stone-100 rounded-2xl px-6 py-12 text-center">
              <p className="text-stone-500">No meetings match "{search}"</p>
            </div>
          ) : (
            <MeetingsTable meetings={filtered} />
          )}
        </div>
      </div>
    </div>
  );
}