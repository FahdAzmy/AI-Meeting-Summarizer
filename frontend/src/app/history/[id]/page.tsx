"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Meeting } from '@/lib/types';
import { SummarySection } from '@/components/detail/SummarySection';
import { ActionItemsTable } from '@/components/detail/ActionItemsTable';
import { TranscriptViewer } from '@/components/detail/TranscriptViewer';
import { SpeakerStats } from '@/components/detail/SpeakerStats';

export default function MeetingDetail() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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

  if (isLoading) {
    return <div className="p-12 text-center text-gray-500 animate-pulse">Loading meeting details...</div>;
  }

  if (!meeting) {
    return null; // Will redirect or show 404
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      <div className="border-b pb-6 mb-6">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Meeting Details</h2>
        <div className="text-gray-500 space-x-4">
          <span>Date: {new Date(meeting.date).toLocaleDateString()}</span>
          <span>Platform: {meeting.platform}</span>
        </div>
      </div>

      <SummarySection summary={meeting.summary} />
      <SpeakerStats stats={meeting.speaker_stats} />
      <ActionItemsTable actionItems={meeting.action_items} decisions={meeting.decisions} />
      <TranscriptViewer transcript={meeting.transcript} />
    </div>
  );
}
