import React, { useState, useMemo } from 'react';
import { Meeting } from '../../lib/types';
import { MeetingRow } from './MeetingRow';

interface MeetingsTableProps {
  meetings: Partial<Meeting>[];
}

type SortKey = 'date' | 'platform' | 'duration_minutes' | 'status';

const headers: { key: SortKey; label: string }[] = [
  { key: 'date', label: 'Date' },
  { key: 'platform', label: 'Platform' },
  { key: 'duration_minutes', label: 'Duration' },
  { key: 'status', label: 'Status' },
];

export function MeetingsTable({ meetings }: MeetingsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('date');
  const [sortDesc, setSortDesc] = useState(true);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDesc(!sortDesc);
    else { setSortKey(key); setSortDesc(true); }
  };

  const sorted = useMemo(() =>
    [...meetings].sort((a, b) => {
      const aVal = a[sortKey] ?? '';
      const bVal = b[sortKey] ?? '';
      if (aVal < bVal) return sortDesc ? 1 : -1;
      if (aVal > bVal) return sortDesc ? -1 : 1;
      return 0;
    }),
    [meetings, sortKey, sortDesc]
  );

  return (
    <div className="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-stone-100">
              {headers.map(({ key, label }) => (
                <th
                  key={key}
                  onClick={() => handleSort(key)}
                  className="px-5 py-3.5 text-left text-[11px] font-bold text-stone-400 uppercase tracking-wider cursor-pointer hover:text-stone-700 select-none transition-colors group"
                >
                  <span className="flex items-center gap-1">
                    {label}
                    <span className={`text-stone-300 transition-opacity ${sortKey === key ? 'opacity-100' : 'opacity-0 group-hover:opacity-50'}`}>
                      {sortDesc ? '↓' : '↑'}
                    </span>
                  </span>
                </th>
              ))}
              <th className="px-5 py-3.5 text-right text-[11px] font-bold text-stone-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((m, i) => (
              <MeetingRow key={m.id || i} meeting={m} isEven={i % 2 === 0} />
            ))}
          </tbody>
        </table>
      </div>
      {/* Table footer */}
      <div className="px-5 py-3 border-t border-stone-100 bg-stone-50/60 text-xs text-stone-400 font-medium">
        {sorted.length} session{sorted.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}
