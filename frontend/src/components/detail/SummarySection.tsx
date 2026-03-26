import React from 'react';

interface SummarySectionProps {
  summary: string | null;
}

export function SummarySection({ summary }: SummarySectionProps) {
  if (!summary) return null;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-4">
      <h3 className="text-xl font-semibold text-gray-900">Summary</h3>
      {/* Real app would use react-markdown here */}
      <div className="text-gray-700 whitespace-pre-wrap">
        {summary}
      </div>
    </div>
  );
}
