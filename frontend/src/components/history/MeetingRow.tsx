import React from 'react';
import Link from 'next/link';
import { Meeting } from '../../lib/types';
import { StatusBadge } from './StatusBadge';
import { PlatformBadge } from '../dashboard/PlatformBadge';

interface MeetingRowProps {
  meeting: Partial<Meeting>;
  isEven?: boolean;
}

export function MeetingRow({ meeting, isEven }: MeetingRowProps) {
  const date = meeting.date
    ? new Date(meeting.date).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
      })
    : '—';

  const time = meeting.date
    ? new Date(meeting.date).toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit',
      })
    : null;

  return (
    <tr className={`border-b border-stone-50 hover:bg-stone-50 transition-colors ${isEven ? 'bg-white' : 'bg-stone-50/30'}`}>
      <td className="px-5 py-3.5">
        <div className="text-sm font-medium text-stone-800">{date}</div>
        {time && <div className="text-xs text-stone-400 mt-0.5">{time}</div>}
      </td>
      <td className="px-5 py-3.5">
        {meeting.platform
          ? <PlatformBadge platform={meeting.platform} />
          : <span className="text-sm text-stone-400">—</span>}
      </td>
      <td className="px-5 py-3.5 text-sm text-stone-600">
        {meeting.duration_minutes ? (
          <span className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {meeting.duration_minutes} min
          </span>
        ) : '—'}
      </td>
      <td className="px-5 py-3.5">
        <StatusBadge status={meeting.status || 'pending'} />
      </td>
      <td className="px-5 py-3.5 text-right">
        <Link
          href={`/history/${meeting.id}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-600 hover:text-stone-900 hover:bg-stone-100 px-2.5 py-1.5 rounded-lg transition-all"
        >
          View details
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </td>
    </tr>
  );
}
