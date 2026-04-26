"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Meeting } from '@/lib/types';
import { SummarySection } from '@/components/detail/SummarySection';
import { ActionItemsTable } from '@/components/detail/ActionItemsTable';
import { TranscriptViewer } from '@/components/detail/TranscriptViewer';
import { SpeakerStats } from '@/components/detail/SpeakerStats';
import { useToast } from '@/components/ui/Toast';

export default function MeetingDetail() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { showToast } = useToast();

  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [isExportingExcel, setIsExportingExcel] = useState(false);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const data = await api.getMeeting(id);
        setMeeting(data);
      } catch (err) {
        console.error(err);
        router.replace(`/history/${id}/not-found`);
      } finally {
        setIsLoading(false);
      }
    };
    fetchDetail();
  }, [id, router]);

  const handleExportPdf = async () => {
    setIsExportingPdf(true);
    try {
      await api.exportMeetingPdf(id);
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
      await api.exportMeetingExcel(id);
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
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-stone-200 border-t-emerald-600 animate-spin" />
          <p className="text-stone-400 text-sm font-medium animate-pulse">Loading meeting details...</p>
        </div>
      </div>
    );
  }

  if (!meeting) {
    return null;
  }

  const formatDate = (date: string | Date) => {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  };

  const formatDuration = (mins: number | null) => {
    if (!mins) return 'N/A';
    const hrs = Math.floor(mins / 60);
    const minsRem = mins % 60;
    if (hrs > 0) return `${hrs}h ${minsRem}m`;
    return `${mins}m`;
  };

  const statusColors: Record<string, string> = {
    completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    processing: 'bg-amber-50 text-amber-700 border-amber-200',
    failed: 'bg-red-50 text-red-700 border-red-200',
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 animate-fade-up">
      <Link
        href="/history"
        className="inline-flex items-center gap-2 text-stone-400 hover:text-stone-600 text-sm font-medium mb-6 transition-colors group"
      >
        <svg className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to History
      </Link>

      <div className="relative mb-8">
        <div className="absolute top-0 right-0 flex items-center gap-3">
          {meeting.status === 'completed' && (
            <>
              <button
                onClick={handleExportPdf}
                disabled={isExportingPdf}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-stone-200 text-stone-700 text-sm font-semibold hover:bg-stone-50 hover:border-stone-300 transition-all shadow-sm active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isExportingPdf ? (
                  <div className="w-4 h-4 rounded-full border-2 border-stone-300 border-t-red-600 animate-spin" />
                ) : (
                  <svg className="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
                {isExportingPdf ? "Exporting..." : "PDF"}
              </button>
              <button
                onClick={handleExportExcel}
                disabled={isExportingExcel}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-stone-900 text-white text-sm font-semibold hover:bg-stone-800 transition-all shadow-lg shadow-stone-900/10 active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isExportingExcel ? (
                  <div className="w-4 h-4 rounded-full border-2 border-stone-600 border-t-white animate-spin" />
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
                {isExportingExcel ? "Exporting..." : "Excel"}
              </button>
            </>
          )}
        </div>

        <div className="pr-48">
          <div className="flex items-center gap-3 mb-3">
            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${statusColors[meeting.status] || 'bg-stone-100 text-stone-600 border-stone-200'}`}>
              {meeting.status?.toUpperCase()}
            </span>
            {meeting.platform && <span className="text-stone-400 text-sm">{meeting.platform}</span>}
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-bold text-stone-900 leading-tight mb-4">
            {meeting.title || 'Meeting'}
          </h1>
          <div className="flex flex-wrap items-center gap-y-2 gap-x-6 text-stone-500 text-sm">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {formatDate(meeting.date)}
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {formatDuration(meeting.duration_minutes)}
            </div>
          </div>
        </div>
      </div>

      <div className="relative">
        <div className="absolute left-8 top-0 bottom-0 w-px bg-gradient-to-b from-stone-200 via-stone-300 to-transparent" />
        
        <div className="space-y-6">
          <SummarySection summary={meeting.summary} />
          <ActionItemsTable actionItems={meeting.action_items} decisions={meeting.decisions} />
          <TranscriptViewer transcript={meeting.transcript} />
        </div>
      </div>
    </div>
  );
}