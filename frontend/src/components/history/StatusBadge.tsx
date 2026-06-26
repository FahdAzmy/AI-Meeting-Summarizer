import React from 'react';
import { MeetingStatus } from '@/lib/types';

interface StatusBadgeProps {
  status: MeetingStatus;
}

const statusConfig: Record<string, { label: string; classes: string }> = {
  completed: { label: 'Completed', classes: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  failed:    { label: 'Failed',    classes: 'bg-red-50 text-red-700 border-red-200' },
  pending:   { label: 'Pending',   classes: 'bg-amber-50 text-amber-700 border-amber-200' },
  joining:   { label: 'Joining',   classes: 'bg-blue-50 text-blue-700 border-blue-200' },
  recording: { label: 'Recording', classes: 'bg-blue-50 text-blue-700 border-blue-200' },
  transcribing: { label: 'Transcribing', classes: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
  summarising: { label: 'Summarising', classes: 'bg-amber-50 text-amber-700 border-amber-200' },
  delivering: { label: 'Delivering', classes: 'bg-purple-50 text-purple-700 border-purple-200' },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] ?? { label: status, classes: 'bg-gray-50 text-gray-600 border-gray-200' };

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium capitalize ${config.classes}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${
        status === 'completed' ? 'bg-emerald-500' :
        status === 'failed'    ? 'bg-red-500' :
        status === 'joining' || status === 'recording' ? 'bg-blue-500' :
                                 'bg-amber-400'
      }`} />
      {config.label}
    </span>
  );
}
