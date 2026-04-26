import React from 'react';
import { ActionItem } from '../../lib/types';

interface ActionItemsTableProps {
  actionItems: ActionItem[];
  decisions: string[];
}

export function ActionItemsTable({ actionItems, decisions }: ActionItemsTableProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="relative bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden animate-fade-up" style={{ animationDelay: '0.3s' }}>
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 to-orange-500" />
        <div className="p-6 sm:p-8">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center">
              <svg className="w-4 h-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-stone-900 font-heading">Action Items</h3>
            <span className="ml-auto px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 text-xs font-semibold">
              {actionItems.length}
            </span>
          </div>
          
          {actionItems.length === 0 ? (
            <p className="text-stone-400 text-sm">No action items recorded.</p>
          ) : (
            <div className="space-y-3">
              {actionItems.map((item, i) => (
                <div key={i} className="p-4 rounded-xl bg-stone-50 border border-stone-100 hover:border-stone-200 hover:bg-stone-100/50 transition-all">
                  <div className="flex items-start justify-between gap-3">
                    <div className="w-5 h-5 rounded-full bg-amber-100 flex items-center justify-center shrink-0 mt-0.5">
                      <svg className="w-3 h-3 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-stone-800 text-sm">{item.task}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs">
                        <span className="flex items-center gap-1 text-stone-500">
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7h" />
                          </svg>
                          {item.assignee}
                        </span>
                        {item.deadline && (
                          <span className="flex items-center gap-1 text-stone-400">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            {item.deadline}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="relative bg-white rounded-2xl shadow-sm border border-stone-100 overflow-hidden animate-fade-up" style={{ animationDelay: '0.4s' }}>
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-rose-500 to-pink-500" />
        <div className="p-6 sm:p-8">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-rose-50 flex items-center justify-center">
              <svg className="w-4 h-4 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-stone-900 font-heading">Decisions</h3>
            <span className="ml-auto px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 text-xs font-semibold">
              {decisions.length}
            </span>
          </div>
          
          {decisions.length === 0 ? (
            <p className="text-stone-400 text-sm">No decisions recorded.</p>
          ) : (
            <div className="space-y-3">
              {decisions.map((decision, i) => (
                <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-stone-50 border border-stone-100">
                  <div className="w-5 h-5 rounded-full bg-rose-100 flex items-center justify-center shrink-0 mt-0.5">
                    <svg className="w-3 h-3 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
                    </svg>
                  </div>
                  <p className="text-stone-700 text-sm leading-relaxed">{decision}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}