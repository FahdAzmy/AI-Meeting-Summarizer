import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { PipelineStatus } from '../../lib/types';

interface StatusPanelProps {
  sessionId: string;
  onComplete: () => void;
}

const steps = [
  'Joining meeting room',
  'Recording audio stream',
  'Transcribing speech',
  'Analyzing content',
  'Generating summary',
  'Finalizing report',
];

export function StatusPanel({ sessionId, onComplete }: StatusPanelProps) {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchStatus = async () => {
      try {
        const data = await api.getStatus(sessionId);
        if (isMounted) {
          setStatus(data);
          if (data.status === 'completed' || data.status === 'failed') {
            onComplete();
          }
        }
      } catch (err) {
        console.error(err);
        if (isMounted) setError('Could not communicate with the pipeline. Please try again.');
      }
    };

    fetchStatus();
    const interval = setInterval(() => {
      if (status?.status !== 'completed' && status?.status !== 'failed' && !error) {
        fetchStatus();
      } else {
        clearInterval(interval);
      }
    }, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [sessionId, status?.status, error, onComplete]);

  if (error) {
    return (
      <div className="flex items-start gap-3 px-4 py-3.5 bg-red-50 border border-red-100 rounded-xl text-sm text-red-700">
        <svg className="w-4 h-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        {error}
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl px-6 py-5 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 rounded-full border-2 border-gray-300 border-t-gray-900 animate-spin" />
          <span className="text-sm text-gray-500">Connecting to pipeline...</span>
        </div>
      </div>
    );
  }

  const progressPct = Math.round((status.step / (status.total_steps || 1)) * 100);
  const currentStepLabel = steps[status.step - 1] ?? status.message;

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Processing pipeline</h3>
        <span className="text-xs font-medium text-gray-500 capitalize bg-gray-100 px-2.5 py-1 rounded-full">
          {status.status}
        </span>
      </div>
      <div className="px-6 py-5 space-y-4">
        {/* Progress bar */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-700 font-medium">{currentStepLabel}</span>
            <span className="text-xs text-gray-400">{status.step} / {status.total_steps}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-gray-900 h-1.5 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        {/* Step list */}
        <div className="grid grid-cols-2 gap-1.5">
          {steps.map((step, i) => {
            const stepNum = i + 1;
            const isDone = stepNum < status.step;
            const isCurrent = stepNum === status.step;
            return (
              <div key={step} className={`flex items-center gap-2 text-xs rounded-lg px-2.5 py-1.5 ${
                isDone    ? 'text-gray-400' :
                isCurrent ? 'text-gray-900 bg-gray-50 font-medium' :
                            'text-gray-300'
              }`}>
                <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] shrink-0 ${
                  isDone    ? 'bg-emerald-100 text-emerald-600' :
                  isCurrent ? 'bg-gray-900 text-white' :
                              'bg-gray-100 text-gray-400'
                }`}>
                  {isDone ? '✓' : stepNum}
                </span>
                {step}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
