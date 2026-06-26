"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Meeting } from "@/lib/types";
import { SummarySection } from "@/components/detail/SummarySection";
import { ActionItemsTable } from "@/components/detail/ActionItemsTable";
import { TranscriptViewer } from "@/components/detail/TranscriptViewer";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/history/StatusBadge";

export default function MeetingDetail() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { showToast } = useToast();

  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [isExportingExcel, setIsExportingExcel] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchDetail = async () => {
      try {
        const data = await api.getMeeting(params.id);
        if (isMounted) setMeeting(data);
      } catch (err) {
        console.error(err);
        router.replace(`/history/${params.id}/not-found`);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    fetchDetail();
    return () => {
      isMounted = false;
    };
  }, [params.id, router]);

  const handleExportPdf = async () => {
    setIsExportingPdf(true);
    try {
      await api.exportMeetingPdf(params.id);
      showToast("PDF downloaded successfully.", "success");
    } catch (error) {
      console.error(error);
      showToast(error instanceof Error ? error.message : "Failed to export PDF.", "error");
    } finally {
      setIsExportingPdf(false);
    }
  };

  const handleExportExcel = async () => {
    setIsExportingExcel(true);
    try {
      await api.exportMeetingExcel(params.id);
      showToast("Excel downloaded successfully.", "success");
    } catch (error) {
      console.error(error);
      showToast(error instanceof Error ? error.message : "Failed to export Excel.", "error");
    } finally {
      setIsExportingExcel(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--primary)]" />
          <p className="text-sm font-medium text-[var(--text-secondary)]">Loading meeting details...</p>
        </div>
      </div>
    );
  }

  if (!meeting) return null;

  const formattedDate = new Date(meeting.date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const duration = (() => {
    if (!meeting.duration_minutes) return "N/A";
    const hours = Math.floor(meeting.duration_minutes / 60);
    const minutes = meeting.duration_minutes % 60;
    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
  })();

  const participantCount = meeting.participants?.length ?? 0;

  return (
    <div className="page-canvas animate-fade-up">
      <div className="mb-6 flex items-center justify-between gap-4">
        <Link href="/history" className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--primary)]">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m15 19-7-7 7-7" />
          </svg>
          History
        </Link>
        {meeting.status === "completed" && (
          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" onClick={handleExportPdf} disabled={isExportingPdf}>
              {isExportingPdf ? "Exporting" : "Export PDF"}
            </Button>
            <Button type="button" variant="outline" onClick={handleExportExcel} disabled={isExportingExcel}>
              {isExportingExcel ? "Exporting" : "Export Excel"}
            </Button>
          </div>
        )}
      </div>

      <div className="mb-6 flex flex-col justify-between gap-4 border-b border-[var(--border)] pb-6 lg:flex-row lg:items-start">
        <div>
          <h1 className="max-w-3xl text-3xl font-bold text-[var(--text-primary)]">{meeting.title || "Meeting"}</h1>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="chip">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3M5 11h14M5 21h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2" />
              </svg>
              {formattedDate}
            </span>
            <span className="chip">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 2m6-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0" />
              </svg>
              {duration}
            </span>
            <span className="chip">
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2M9.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M22 21v-2a4 4 0 0 0-3-3.9" />
              </svg>
              {participantCount} attendees
            </span>
          </div>
        </div>
        <StatusBadge status={meeting.status} />
      </div>

      {meeting.status === "failed" && meeting.error_message && (
        <div className="mb-6 rounded-lg border border-[var(--danger)]/20 bg-[var(--danger)]/5 p-4 text-sm text-[var(--danger)]">
          <p className="font-semibold">Pipeline failed</p>
          <p className="mt-1">{meeting.error_message}</p>
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 space-y-6 xl:col-span-8">
          <SummarySection summary={meeting.summary} />
          <ActionItemsTable actionItems={meeting.action_items} decisions={meeting.decisions} />
          <TranscriptViewer transcript={meeting.transcript} />
        </div>

        <aside className="col-span-12 space-y-6 xl:col-span-4">
          <section className="panel overflow-hidden">
            <div className="panel-header">
              <h2 className="text-sm font-semibold text-[var(--text-primary)]">Meeting Info</h2>
            </div>
            <dl className="divide-y divide-[var(--border)] text-sm">
              <div className="flex items-center justify-between gap-4 px-5 py-4">
                <dt className="text-[var(--text-secondary)]">Platform</dt>
                <dd className="font-medium text-[var(--text-primary)]">{meeting.platform || "--"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 px-5 py-4">
                <dt className="text-[var(--text-secondary)]">Session ID</dt>
                <dd className="truncate font-mono text-xs text-[var(--text-primary)]">{meeting.session_id}</dd>
              </div>
              <div className="flex items-center justify-between gap-4 px-5 py-4">
                <dt className="text-[var(--text-secondary)]">Participants</dt>
                <dd className="font-medium text-[var(--text-primary)]">{participantCount}</dd>
              </div>
            </dl>
          </section>
        </aside>
      </div>
    </div>
  );
}
