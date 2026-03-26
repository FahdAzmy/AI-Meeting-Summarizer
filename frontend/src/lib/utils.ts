import { Platform } from './types';

export function detectPlatform(url: string): Platform | null {
  if (!url) return null;
  const lowerUrl = url.toLowerCase();
  
  if (lowerUrl.includes('meet.google.com')) return 'google_meet';
  if (lowerUrl.includes('zoom.us')) return 'zoom';
  if (lowerUrl.includes('teams.microsoft.com')) return 'teams';
  
  return null;
}

export function isValidMeetingUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return detectPlatform(parsed.href) !== null;
  } catch {
    return false;
  }
}
