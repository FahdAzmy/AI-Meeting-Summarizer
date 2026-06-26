import React from 'react';
import { SpeakerStatsObject } from '@/lib/types';

interface SpeakerStatsProps {
  stats: SpeakerStatsObject | null;
}

export function SpeakerStats({ stats }: SpeakerStatsProps) {
  if (!stats || Object.keys(stats).length === 0) return null;

  const speakers = Object.entries(stats);

  return (
    <div className="panel overflow-hidden animate-fade-up" style={{ animationDelay: '0.2s' }}>
      <div className="panel-header flex items-center gap-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary-soft)] text-[var(--primary)]">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H8m8 0v-2c0-2.828-2.238-5-5-5H8c-2.762 0-5 2.172-5 5v2m8 0h5m-5 0h5m-5 0v-2c0-2.828-2.238-5-5-5H8c-2.762 0-5 2.172-5 5v2" />
          </svg>
        </span>
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Participants</h3>
      </div>

      <div className="space-y-4 p-6">
        {speakers.map(([speaker, data]) => (
          <div key={speaker}>
            <div className="mb-2 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--surface-recessed)] text-xs font-bold text-[var(--text-secondary)]">
                  {speaker.charAt(0).toUpperCase()}
                </span>
                <span className="text-sm font-medium text-[var(--text-primary)]">{speaker}</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-[var(--text-secondary)]">{data.duration}s</span>
                <span className="text-[var(--border-strong)]">·</span>
                <span className="font-semibold text-[var(--text-primary)]">{data.percentage}%</span>
              </div>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--surface-recessed)]">
              <div
                className="h-full rounded-full bg-[var(--primary)] transition-all duration-500"
                style={{ width: `${data.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}