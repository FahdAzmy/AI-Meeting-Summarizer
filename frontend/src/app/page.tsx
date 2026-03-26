"use client";

import { useState } from "react";
import { MeetingForm } from "@/components/dashboard/MeetingForm";
import { StatusPanel } from "@/components/dashboard/StatusPanel";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { useRouter } from "next/navigation";

const features = [
  { icon: "🎙️", text: "Auto-transcription" },
  { icon: "✨", text: "AI summaries" },
  { icon: "📋", text: "Action items" },
];

export default function Dashboard() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { showToast } = useToast();
  const router = useRouter();

  const handleJoinMeeting = async (link: string, emails: string[]) => {
    setIsLoading(true);
    try {
      const response = await api.joinMeeting(link, emails);
      setSessionId(response.session_id);
      showToast("Successfully initiated processing pipeline.", "success");
    } catch (error) {
      console.error(error);
      showToast("Failed to join meeting. Please check backend connection.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePipelineComplete = () => {
    showToast("Meeting processing completed!", "success");
    setTimeout(() => router.push("/history"), 2000);
  };

  return (
    <div className="flex flex-col items-center pt-16 pb-24 px-8 min-h-full">
      {/* Hero text */}
      <div className="text-center mb-10 animate-fade-up w-full max-w-xl">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 bg-white border border-stone-200 rounded-full px-3.5 py-1.5 text-xs font-semibold text-stone-600 shadow-sm mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          AI pipeline active
        </div>

        <h1 className="font-heading text-4xl font-extrabold text-stone-900 leading-tight tracking-tight">
          Turn any meeting<br />
          <span className="text-stone-400 font-medium">into structured knowledge.</span>
        </h1>

        <p className="mt-4 text-sm text-stone-500 leading-relaxed max-w-sm mx-auto">
          Share your meeting link and let the AI do the rest — join, listen, transcribe, and summarize in minutes.
        </p>

        {/* Feature pills */}
        <div className="flex items-center justify-center gap-2 mt-5 flex-wrap">
          {features.map(f => (
            <span key={f.text} className="inline-flex items-center gap-1.5 px-3 py-1 bg-white border border-stone-200 rounded-full text-xs font-medium text-stone-600 shadow-sm">
              {f.icon} {f.text}
            </span>
          ))}
        </div>
      </div>

      {/* Form */}
      <div className="w-full max-w-xl animate-fade-up animation-delay-100">
        <MeetingForm onSubmit={handleJoinMeeting} isLoading={isLoading} />
      </div>

      {/* Status panel */}
      {sessionId && (
        <div className="w-full max-w-xl mt-5 animate-fade-up animation-delay-200">
          <StatusPanel sessionId={sessionId} onComplete={handlePipelineComplete} />
        </div>
      )}

      {/* Supported platforms */}
      {!sessionId && (
        <div className="mt-8 flex items-center gap-3 animate-fade-up animation-delay-200">
          <span className="text-xs text-stone-400">Works with</span>
          {["Google Meet", "Zoom", "MS Teams"].map(p => (
            <span key={p} className="text-xs font-medium text-stone-500 bg-white border border-stone-200 rounded px-2 py-0.5 shadow-sm">
              {p}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
