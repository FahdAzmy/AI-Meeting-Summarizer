import React, { useState } from 'react';

interface TranscriptViewerProps {
  transcript: string | null;
}

export function TranscriptViewer({ transcript }: TranscriptViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!transcript) return null;

  const lines = transcript.split('\n').filter(line => line.trim());

  return (
    <div className="relative bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden animate-fade-up" style={{ animationDelay: '0.5s' }}>
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-slate-500 to-stone-500" />
      <div className="p-6 sm:p-8">
        <div className="flex items-center justify-between gap-4 mb-5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-stone-100 flex items-center justify-center">
              <svg className="w-4 h-4 text-stone-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-5.086-1.386C8.304 18.204 6 15.918 6 13c0-2.761 2.239-5 5-5s5 2.239 5 5c0 1.054-.328 2.024-.889 2.833M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-5.086-1.386C8.304 18.204 6 15.918 6 13" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-stone-900 font-heading">Transcript</h3>
            <span className="px-2 py-0.5 rounded-full bg-stone-100 text-stone-600 text-xs font-semibold">
              {lines.length} lines
            </span>
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-stone-100 text-stone-600 text-sm font-medium hover:bg-stone-200 transition-colors"
          >
            {isExpanded ? (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
                Collapse
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
                Expand
              </>
            )}
          </button>
        </div>
        
        {isExpanded && (
          <div className="bg-stone-50 rounded-xl border border-stone-100 max-h-80 overflow-y-auto">
            <div className="p-4 font-mono text-sm text-stone-700 leading-relaxed">
              {lines.map((line, i) => (
                <div key={i} className="py-1.5 border-b border-stone-100 last:border-0">
                  {line}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}