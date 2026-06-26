import React, { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { PipelineStatus } from "@/lib/types";

interface StatusPanelProps {
  sessionId: string;
  onComplete: () => void;
}

const steps = [
  "Joining meeting room",
  "Recording audio stream",
  "Transcribing speech",
  "Analyzing content",
  "Generating summary",
  "Finalizing report",
];

export function StatusPanel({ sessionId, onComplete }: StatusPanelProps) {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const onCompleteRef = useRef(onComplete);
  const isFetchingRef = useRef(false);

  onCompleteRef.current = onComplete;

  useEffect(() => {
    let isMounted = true;
    let interval: NodeJS.Timeout;

    const fetchStatus = async () => {
      if (isFetchingRef.current) return;
      isFetchingRef.current = true;

      try {
        const data = await api.getStatus(sessionId);
        if (isMounted) {
          setStatus(data);
          if (data.status === "completed" || data.status === "failed") {
            clearInterval(interval);
            onCompleteRef.current();
          }
        }
      } catch (err) {
        console.error(err);
        if (isMounted) {
          setError("Could not communicate with the pipeline. Please try again.");
          clearInterval(interval);
        }
      } finally {
        isFetchingRef.current = false;
      }
    };

    fetchStatus();
    interval = setInterval(fetchStatus, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [sessionId]);

  if (error) {
    return (
      <div className="flex items-start gap-3 rounded-lg border border-[var(--danger)]/20 bg-[var(--danger)]/5 px-4 py-3.5 text-sm text-[var(--danger)]">
        <svg className="mt-0.5 h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0" />
        </svg>
        {error}
      </div>
    );
  }

  if (!status) {
    return (
      <div className="panel px-6 py-5">
        <div className="flex items-center gap-3">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--primary)]" />
          <span className="text-sm text-[var(--text-secondary)]">Connecting to pipeline...</span>
        </div>
      </div>
    );
  }

  const progressPct = Math.round((status.step / (status.total_steps || 1)) * 100);
  const currentStepLabel = steps[status.step - 1] ?? status.message;

  return (
    <div className="panel overflow-hidden">
      <div className="panel-header flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Processing pipeline</h3>
        <span className="rounded-full bg-[var(--surface)] px-2.5 py-1 text-xs font-medium capitalize text-[var(--text-secondary)] ring-1 ring-[var(--border)]">
          {status.status}
        </span>
      </div>
      <div className="space-y-4 px-6 py-5">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-[var(--text-primary)]">{currentStepLabel}</span>
            <span className="text-xs text-[var(--text-muted)]">{status.step} / {status.total_steps}</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--surface-recessed)]">
            <div
              className="h-1.5 rounded-full bg-[var(--primary)] transition-all duration-700 ease-out"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-1.5">
          {steps.map((step, index) => {
            const stepNum = index + 1;
            const isDone = stepNum < status.step;
            const isCurrent = stepNum === status.step;

            return (
              <div
                key={step}
                className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs ${
                  isDone
                    ? "text-[var(--text-muted)]"
                    : isCurrent
                      ? "bg-[var(--surface-recessed)] font-medium text-[var(--text-primary)]"
                      : "text-[var(--border-strong)]"
                }`}
              >
                <span
                  className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] ${
                    isDone
                      ? "bg-emerald-100 text-emerald-700"
                      : isCurrent
                        ? "bg-[var(--primary)] text-white"
                        : "bg-[var(--surface-recessed)] text-[var(--text-muted)]"
                  }`}
                >
                  {isDone ? (
                    <svg className="h-2.5 w-2.5" fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={2}>
                      <path d="M2.5 6.5 5 9l4.5-6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    stepNum
                  )}
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
