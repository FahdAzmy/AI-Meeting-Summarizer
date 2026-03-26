import React from 'react';
import { StorageBackend } from '../../lib/types';

interface StorageToggleProps {
  value: StorageBackend;
  onChange: (value: StorageBackend) => void;
}

export function StorageToggle({ value, onChange }: StorageToggleProps) {
  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">Storage Backend</label>
      <div className="flex gap-4">
        {['database', 'google_sheets'].map((option) => (
          <label key={option} className="flex items-center gap-2 cursor-pointer bg-gray-50 border p-3 rounded-md w-full sm:w-1/2 hover:bg-gray-100 transition-colors">
            <input 
              type="radio" 
              name="storage" 
              value={option} 
              checked={value === option} 
              onChange={() => onChange(option as StorageBackend)}
              className="text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-gray-900 capitalize">
              {option.replace('_', ' ')}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}
