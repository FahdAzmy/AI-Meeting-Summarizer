"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { MeetingForm } from "@/components/dashboard/MeetingForm";
import { StatusPanel } from "@/components/dashboard/StatusPanel";
import { useToast } from "@/components/ui/Toast";
import { WelcomeDialog } from "@/components/ui/WelcomeDialog";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { CreateMeetingPayload, DashboardStats } from "@/lib/types";

function metricLabel(key: string) {
  return key
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function DashboardPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStatsLoading, setIsStatsLoading] = useState(true);
  const { showToast } = useToast();
  const router = useRouter();
  const { user, isAuthenticated, isReady } = useAuth();

  useEffect(() => {
    if (isReady && !isAuthenticated) router.replace("/login");
  }, [isReady, isAuthenticated, router]);

  useEffect(() => {
    let isMounted = true;
    async function loadStats() {
      if (!isAuthenticated) return;
      try {
        setIsStatsLoading(true);
        const data = await api.getDashboard();
        if (isMounted) setStats(data);
      } catch (error) {
        console.error(error);
        if (isMounted) showToast("Failed to load dashboard statistics.", "error");
      } finally {
        if (isMounted) setIsStatsLoading(false);
      }
    }
    loadStats();
    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, showToast]);

  const handleJoinMeeting = async (payload: CreateMeetingPayload) => {
    setIsLoading(true);
    try {
      const response = await api.joinMeeting(payload);
      setSessionId(response.session_id);
      showToast("Successfully initiated processing pipeline.", "success");
    } catch (error) {
      console.error(error);
      showToast("Failed to start meeting. Please check backend connection.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePipelineComplete = useCallback(() => {
    showToast("Meeting processing completed!", "success");
    setTimeout(() => router.push("/history"), 2000);
  }, [showToast, router]);

  if (!isReady || !isAuthenticated) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-[var(--text-secondary)]">Loading workspace...</div>;
  }

  const metricEntries = stats
    ? Object.entries(stats).filter(([, value]) => typeof value === "number" || typeof value === "string" || value === null)
    : [];

  return (
    <div className="page-canvas animate-fade-up">
      <WelcomeDialog />
      <div className="space-y-6">
        <div className="flex flex-col justify-between gap-4 border-b border-[var(--border)] pb-6 lg:flex-row lg:items-end">
          <div>
            <p className="label-caps">
              {user?.role === "hr" ? "Company dashboard" : "Team dashboard"}
            </p>
            <h1 className="mt-2 text-3xl font-bold text-[var(--text-primary)]">
              Welcome, {user?.name}
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-[var(--text-secondary)]">
              {user?.role === "hr"
                ? "Track teams, members, meetings, and workspace activity."
                : "Monitor your team participation and open action items."}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {isStatsLoading
            ? Array.from({ length: user?.role === "hr" ? 5 : 3 }).map((_, index) => (
                <div key={index} className="panel h-28 animate-pulse" />
              ))
            : metricEntries.length === 0 ? (
              <div className="panel col-span-full p-5 text-center text-sm text-[var(--text-secondary)]">
                No statistics available yet. Start your first meeting to see data.
              </div>
            ) : metricEntries.map(([key, value]) => (
                <div key={key} className="panel p-5">
                  <p className="label-caps">{metricLabel(key)}</p>
                  <p className="mt-3 text-3xl font-bold text-[var(--text-primary)]">{value ?? "None"}</p>
                </div>
              ))}
        </div>

        <div className="grid lg:grid-cols-[minmax(0,1fr)_360px] gap-6 items-start">
          <MeetingForm onSubmit={handleJoinMeeting} isLoading={isLoading} />
          <div className="space-y-4">
            {sessionId ? (
              <StatusPanel sessionId={sessionId} onComplete={handlePipelineComplete} />
            ) : (
              <div className="panel overflow-hidden">
                <div className="panel-header">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Quick start</h3>
                </div>
                <div className="space-y-4 px-5 py-4">
                  <ol className="space-y-3">
                    {[
                      { step: "1", label: "Paste a meeting link (Google Meet, Zoom, Teams)" },
                      { step: "2", label: "Select teams or members to notify" },
                      { step: "3", label: "Click \"Start session\" and watch the pipeline" },
                    ].map((item) => (
                      <li key={item.step} className="flex items-start gap-3 text-sm">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--primary-soft)] text-[10px] font-bold text-[var(--primary)]">
                          {item.step}
                        </span>
                        <span className="pt-0.5 text-[var(--text-secondary)]">{item.label}</span>
                      </li>
                    ))}
                  </ol>
                  <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-recessed)] px-3 py-2.5">
                    <p className="text-xs font-medium text-[var(--text-primary)]">Did you know?</p>
                    <p className="mt-0.5 text-xs text-[var(--text-secondary)]">
                      You can press <kbd className="rounded border border-[var(--border)] bg-[var(--surface)] px-1 py-0.5 font-mono text-[10px]">Alt+N</kbd> to jump here from anywhere.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
