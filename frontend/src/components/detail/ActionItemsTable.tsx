import React from 'react';
import { ActionItem } from '../../lib/types';

interface ActionItemsTableProps {
  actionItems: ActionItem[];
  decisions: string[];
}

export function ActionItemsTable({ actionItems, decisions }: ActionItemsTableProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Action Items</h3>
        {actionItems.length === 0 ? (
          <p className="text-gray-500">No action items.</p>
        ) : (
          <ul className="space-y-3">
            {actionItems.map((item, i) => (
              <li key={i} className="flex flex-col p-3 bg-gray-50 rounded-lg">
                <span className="font-medium text-gray-900">{item.task}</span>
                <span className="text-sm text-gray-500 mt-1">
                  Assignee: {item.assignee} {item.deadline && `| Due: ${item.deadline}`}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Decisions</h3>
        {decisions.length === 0 ? (
          <p className="text-gray-500">No decisions recorded.</p>
        ) : (
          <ul className="list-disc pl-5 space-y-2 text-gray-700">
            {decisions.map((decision, i) => (
              <li key={i}>{decision}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
