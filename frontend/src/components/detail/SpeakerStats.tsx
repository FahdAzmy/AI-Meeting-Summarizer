import React from 'react';
import { SpeakerStatsObject } from '../../lib/types';

interface SpeakerStatsProps {
  stats: SpeakerStatsObject | null;
}

export function SpeakerStats({ stats }: SpeakerStatsProps) {
  if (!stats || Object.keys(stats).length === 0) return null;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">Speaker Stats</h3>
      <div className="space-y-4">
        {Object.entries(stats).map(([speaker, data]) => (
          <div key={speaker}>
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-gray-700">{speaker}</span>
              <span className="text-gray-500">{data.duration}s ({data.percentage}%)</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full"
                style={{ width: `${data.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
