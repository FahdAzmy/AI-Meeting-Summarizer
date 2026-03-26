import React, { useState } from 'react';
import { Button } from '../ui/Button';

interface TranscriptViewerProps {
  transcript: string | null;
}

export function TranscriptViewer({ transcript }: TranscriptViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!transcript) return null;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mt-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold text-gray-900">Transcript</h3>
        <Button variant="outline" onClick={() => setIsExpanded(!isExpanded)}>
          {isExpanded ? 'Collapse' : 'Expand'}
        </Button>
      </div>
      
      {isExpanded && (
        <div className="bg-gray-50 p-4 rounded-md border border-gray-100 max-h-96 overflow-y-auto whitespace-pre-wrap font-mono text-sm text-gray-800 leading-relaxed">
          {transcript}
        </div>
      )}
    </div>
  );
}
