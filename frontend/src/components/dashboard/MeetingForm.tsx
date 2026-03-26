import React, { useState } from 'react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { detectPlatform, isValidMeetingUrl } from '../../lib/utils';
import { PlatformBadge } from './PlatformBadge';

interface MeetingFormProps {
  onSubmit: (link: string, emails: string[]) => void;
  isLoading?: boolean;
}

export function MeetingForm({ onSubmit, isLoading }: MeetingFormProps) {
  const [link, setLink] = useState('');
  const [emails, setEmails] = useState('');
  const [error, setError] = useState('');

  const detectedPlatform = detectPlatform(link);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!isValidMeetingUrl(link)) {
      setError('Please enter a valid meeting link (Google Meet, Zoom, or MS Teams).');
      return;
    }
    const emailList = emails.split(',').map(e => e.trim()).filter(Boolean);
    onSubmit(link, emailList);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-2xl shadow-[0_2px_20px_rgba(0,0,0,0.07)] border border-stone-200 overflow-hidden"
    >
      {/* Card header */}
      <div className="px-6 pt-6 pb-5 border-b border-stone-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-stone-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-stone-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-stone-900 leading-none">Meeting link</h2>
            <p className="text-xs text-stone-400 mt-0.5">Paste a link to get started</p>
          </div>
        </div>
      </div>

      {/* Fields */}
      <div className="px-6 py-5 space-y-4">
        {/* Link field */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-stone-600 uppercase tracking-wider">
            Meeting URL
          </label>
          <div className="flex gap-2 items-center">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <svg className="w-4 h-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
              <Input
                type="url"
                placeholder="https://meet.google.com/abc-defg-hij"
                value={link}
                onChange={(e) => setLink(e.target.value)}
                className="pl-9"
              />
            </div>
            {detectedPlatform && <PlatformBadge platform={detectedPlatform} />}
          </div>
          {error && (
            <div className="flex items-center gap-1.5 text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mt-1">
              <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {error}
            </div>
          )}
        </div>

        {/* Participants field */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-stone-600 uppercase tracking-wider">
              Participants
            </label>
            <span className="text-[10px] text-stone-400 font-medium bg-stone-100 px-2 py-0.5 rounded-full">Optional</span>
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
              <svg className="w-4 h-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <Input
              type="text"
              placeholder="dev@example.com, pm@example.com"
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              className="pl-9"
            />
          </div>
          <p className="text-[11px] text-stone-400">Comma-separated. Participants receive the summary via email.</p>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 bg-stone-50 border-t border-stone-100 flex items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 text-[11px] text-stone-400">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Bot joins anonymously and never records video.
        </div>
        <Button type="submit" disabled={isLoading || !link} className="shrink-0">
          {isLoading ? (
            <>
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Starting...
            </>
          ) : (
            <>
              Start session
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
