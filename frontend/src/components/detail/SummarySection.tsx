import React from 'react';

interface SummarySectionProps {
  summary: string | null;
}

export function SummarySection({ summary }: SummarySectionProps) {
  if (!summary) return null;

  return (
    <div className="relative bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden animate-fade-up" style={{ animationDelay: '0.1s' }}>
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500" />
      <div className="p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
            <svg className="w-4 h-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h12a2 2 0 012 2v12a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-stone-900 font-heading">Summary</h3>
        </div>
        <div className="prose prose-stone max-w-none">
          <div className="text-stone-700 leading-relaxed whitespace-pre-wrap text-[15px]">
            {summary}
          </div>
        </div>
      </div>
    </div>
  );
}