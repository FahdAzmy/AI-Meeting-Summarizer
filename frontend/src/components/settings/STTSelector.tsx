import React from 'react';
import { STTProvider } from '../../lib/types';

interface STTSelectorProps {
  value: STTProvider;
  onChange: (value: STTProvider) => void;
}

export function STTSelector({ value, onChange }: STTSelectorProps) {
  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">Speech-to-Text Provider</label>
      <select 
        value={value} 
        onChange={(e) => onChange(e.target.value as STTProvider)}
        className="block w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
      >
        <option value="whisper">Whisper (OpenAI)</option>
        <option value="deepgram">Deepgram</option>
        <option value="assemblyai">AssemblyAI</option>
      </select>
    </div>
  );
}
