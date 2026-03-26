import React from 'react';
import { MeetingStatus } from '../../lib/types';

interface StatusBadgeProps {
  status: MeetingStatus;
}

const statusConfig: Record<string, { label: string; classes: string }> = {
  completed: { label: 'Completed', classes: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
  failed:    { label: 'Failed',    classes: 'bg-red-50 text-red-700 border-red-100' },
  pending:   { label: 'Pending',   classes: 'bg-amber-50 text-amber-700 border-amber-100' },
  joining:   { label: 'Joining',   classes: 'bg-blue-50 text-blue-700 border-blue-100' },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] ?? { label: status, classes: 'bg-gray-50 text-gray-600 border-gray-200' };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium border capitalize ${config.classes}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${
        status === 'completed' ? 'bg-emerald-500' :
        status === 'failed'    ? 'bg-red-500' :
        status === 'joining'   ? 'bg-blue-500' :
                                 'bg-amber-400'
      }`} />
      {config.label}
    </span>
  );
}
