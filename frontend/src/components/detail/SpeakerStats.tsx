import React from 'react';
import { SpeakerStatsObject } from '../../lib/types';

interface SpeakerStatsProps {
  stats: SpeakerStatsObject | null;
}

export function SpeakerStats({ stats }: SpeakerStatsProps) {
  if (!stats || Object.keys(stats).length === 0) return null;

  const speakers = Object.entries(stats);
  const maxDuration = Math.max(...speakers.map(([, d]) => d.duration));

  return (
    <div className="relative bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden animate-fade-up" style={{ animationDelay: '0.2s' }}>
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-violet-500 to-purple-500" />
      <div className="p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-violet-50 flex items-center justify-center">
            <svg className="w-4 h-4 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H8m8 0v-2c0-2.828-2.238-5-5-5H8c-2.762 0-5 2.172-5 5v2m8 0h5m-5 0h5m-5 0v-2c0-2.828-2.238-5-5-5H8c-2.762 0-5 2.172-5 5v2" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-stone-900 font-heading">Participants</h3>
        </div>
        
        <div className="grid gap-4">
          {speakers.map(([speaker, data], index) => (
            <div key={speaker} className="group">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-stone-100 flex items-center justify-center text-sm font-semibold text-stone-600">
                    {speaker.charAt(0).toUpperCase()}
                  </div>
                  <span className="font-medium text-stone-800">{speaker}</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-stone-500">{data.duration}s</span>
                  <span className="text-stone-300">·</span>
                  <span className="font-semibold text-stone-700">{data.percentage}%</span>
                </div>
              </div>
              <div className="w-full h-2 bg-stone-100 rounded-full overflow-hidden">
                <div 
                  className="h-full rounded-full bg-gradient-to-r from-violet-500 to-purple-500 transition-all duration-500 group-hover:shadow-md"
                  style={{ width: `${data.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}