import React from "react";
import { ActionItem } from "@/lib/types";

interface ActionItemsTableProps {
  actionItems: ActionItem[];
  decisions: string[];
}

export function ActionItemsTable({ actionItems, decisions }: ActionItemsTableProps) {
  return (
    <section className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(280px,0.8fr)]">
      <div className="panel overflow-hidden">
        <div className="panel-header flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Action Items</h2>
          <span className="chip">{actionItems.length}</span>
        </div>
        {actionItems.length === 0 ? (
          <div className="px-6 py-10 text-sm text-[var(--text-secondary)]">No action items recorded.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] bg-[var(--surface-recessed)]">
                  <th className="px-6 py-3 text-[11px] font-bold uppercase text-[var(--text-secondary)]">Assignee</th>
                  <th className="px-6 py-3 text-[11px] font-bold uppercase text-[var(--text-secondary)]">Task</th>
                  <th className="px-6 py-3 text-[11px] font-bold uppercase text-[var(--text-secondary)]">Due Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {actionItems.map((item, index) => (
                  <tr key={`${item.task}-${index}`} className="transition-colors hover:bg-[var(--surface-low)]">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--primary-soft)] text-xs font-bold text-[var(--primary)]">
                          {(item.assignee || "?").slice(0, 1).toUpperCase()}
                        </span>
                        <span className="font-medium text-[var(--text-primary)]">{item.assignee || "Unassigned"}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-[var(--text-primary)]">{item.task}</td>
                    <td className="px-6 py-4 text-[var(--text-secondary)]">{item.deadline || "--"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="panel overflow-hidden">
        <div className="panel-header flex items-center justify-between bg-[var(--surface-ai)]">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">Key Decisions</h2>
          <span className="rounded-full border border-[rgb(217_119_6_/_0.30)] bg-[var(--surface-ai)] px-2.5 py-1 text-xs font-medium text-[var(--ai-accent)]">
            {decisions.length}
          </span>
        </div>
        <div className="space-y-3 p-5">
          {decisions.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">No decisions recorded.</p>
          ) : (
            decisions.map((decision, index) => (
              <div key={`${decision}-${index}`} className="flex gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--surface-ai)] text-[var(--ai-accent)]">
                  <svg className="h-3 w-3" fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={2}>
                    <path d="M2.5 6.5 5 9l4.5-6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                <p className="text-sm leading-6 text-[var(--text-primary)]">{decision}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
