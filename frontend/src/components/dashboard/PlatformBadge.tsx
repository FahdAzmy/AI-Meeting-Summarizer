import React from 'react';

interface PlatformBadgeProps {
  platform: string;
}

const getPlatformInfo = (platform: string) => {
  const p = platform?.toLowerCase() || '';
  if (p.includes('google') || p.includes('meet')) {
    return { label: 'Google Meet', classes: 'bg-blue-50 text-blue-700 border-blue-200' };
  }
  if (p.includes('zoom')) {
    return { label: 'Zoom', classes: 'bg-blue-50 text-blue-700 border-blue-200' };
  }
  if (p.includes('teams') || p.includes('microsoft')) {
    return { label: 'MS Teams', classes: 'bg-indigo-50 text-indigo-700 border-indigo-200' };
  }
  return { label: platform || 'Unknown', classes: 'bg-stone-100 text-stone-600 border-stone-200' };
};

export function PlatformBadge({ platform }: PlatformBadgeProps) {
  const { label, classes } = getPlatformInfo(platform);

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${classes}`}>
      {label}
    </span>
  );
}
