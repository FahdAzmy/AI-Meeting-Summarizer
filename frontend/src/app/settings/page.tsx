"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Settings } from '@/lib/types';
import { StorageToggle } from '@/components/settings/StorageToggle';
import { STTSelector } from '@/components/settings/STTSelector';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/Toast';

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    let isMounted = true;
    api.getSettings()
      .then(data => {
        if (isMounted) setSettings(data);
      })
      .catch((err) => {
        console.error(err);
        if (isMounted) showToast("Failed to load settings from server.", "error");
      });
    return () => { isMounted = false; };
  }, [showToast]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;

    setIsSaving(true);
    try {
      const updated = await api.updateSettings(settings);
      setSettings(updated);
      showToast("Settings updated successfully.", "success");
    } catch (error) {
      console.error(error);
      showToast("Failed to save settings.", "error");
    } finally {
      setIsSaving(false);
    }
  };

  if (!settings) {
    return <div className="p-12 text-center text-gray-500 animate-pulse">Loading settings...</div>;
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-12">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Global Settings</h2>
        <p className="text-gray-600">
          Configure how the AI assistant processes and stores your meetings.
        </p>
      </div>

      <form onSubmit={handleSave} className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 space-y-8">
        <StorageToggle 
          value={settings.storage_backend} 
          onChange={(v) => setSettings({ ...settings, storage_backend: v })} 
        />
        
        <STTSelector 
          value={settings.stt_provider} 
          onChange={(v) => setSettings({ ...settings, stt_provider: v })} 
        />

        <div className="space-y-4 pt-4 border-t border-gray-100">
          <h3 className="text-lg font-medium text-gray-900">Email Configuration</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sender Email</label>
            <Input 
              type="email" 
              value={settings.email_sender} 
              onChange={(e) => setSettings({ ...settings, email_sender: e.target.value })} 
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email Password (Leave blank to keep unchanged)</label>
            <Input 
              type="password" 
              value={settings.email_password || ''} 
              onChange={(e) => setSettings({ ...settings, email_password: e.target.value })} 
              placeholder="••••••••"
            />
          </div>
        </div>

        <div className="pt-4 border-t border-gray-100 flex justify-end">
          <Button type="submit" disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </form>
    </div>
  );
}
