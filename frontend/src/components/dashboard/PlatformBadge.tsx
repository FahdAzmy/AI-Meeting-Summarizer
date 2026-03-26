import React from 'react';
import { Platform } from '../../lib/types';

interface PlatformBadgeProps {
  platform: Platform;
}

const config: Record<Platform, { label: string; classes: string }> = {
  google_meet: { label: 'Google Meet', classes: 'bg-gray-100 text-gray-700 border-gray-200' },
  zoom:        { label: 'Zoom',        classes: 'bg-gray-100 text-gray-700 border-gray-200' },
  teams:       { label: 'MS Teams',   classes: 'bg-gray-100 text-gray-700 border-gray-200' },
};

export function PlatformBadge({ platform }: PlatformBadgeProps) {
  const { label, classes } = config[platform] ?? { label: platform, classes: 'bg-gray-100 text-gray-700 border-gray-200' };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border ${classes}`}>
      {label}
    </span>
  );
}
