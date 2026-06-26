"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Member, Team } from "@/lib/types";
import { useToast } from "@/components/ui/Toast";

export default function TeamDetailPage() {
  const params = useParams<{ id: string }>();
  const { user, isAuthenticated, isReady } = useAuth();
  const { showToast } = useToast();
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [form, setForm] = useState({ name: "", email: "" });
  const [editingId, setEditingId] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadTeam() {
      if (!isAuthenticated) return;
      const [teamData, memberData] = await Promise.all([
        api.getTeam(params.id),
        api.getMembers(params.id),
      ]);
      if (isMounted) {
        setTeam(teamData);
        setMembers(memberData);
      }
    }
    loadTeam();
    return () => {
      isMounted = false;
    };
  }, [params.id, isAuthenticated]);

  const resetForm = () => {
    setEditingId(null);
    setForm({ name: "", email: "" });
  };

  const submitMember = async (event: FormEvent) => {
    event.preventDefault();
    if (!team) return;
    try {
      if (editingId) {
        const updated = await api.updateMember(editingId, form);
        setMembers((current) => current.map((member) => (member.id === updated.id ? updated : member)));
        showToast("Member updated successfully.", "success");
      } else {
        const created = await api.createMember({ ...form, team_id: team.id });
        setMembers((current) => [...current, created]);
        showToast("Member added successfully.", "success");
      }
      resetForm();
    } catch (error) {
      console.error(error);
      showToast(error instanceof Error ? error.message : "Operation failed", "error");
    }
  };

  const deleteMember = async (id: string) => {
    try {
      await api.deleteMember(id);
      setMembers((current) => current.filter((member) => member.id !== id));
      showToast("Member deleted successfully.", "success");
    } catch (error) {
      console.error(error);
      showToast("Failed to delete member.", "error");
    }
  };

  const handleAssignLeader = async (memberId: string) => {
    if (!team) return;
    try {
      const updated = await api.assignLeader(team.id, memberId);
      setTeam(updated);
      showToast("Team leader assigned successfully.", "success");
    } catch (error) {
      console.error(error);
      showToast("Failed to assign team leader.", "error");
    }
  };

  if (!isReady || !isAuthenticated) {
    return <div className="p-8 text-sm text-[var(--text-secondary)]">Loading workspace...</div>;
  }

  return (
    <div className="page-canvas animate-fade-up">
      <div className="space-y-6">
        <header className="border-b border-[var(--border)] pb-6">
          <Link href="/teams" className="mb-4 flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:text-[var(--primary)]">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m15 19-7-7 7-7" />
            </svg>
            Teams
          </Link>
          <p className="label-caps">Team detail</p>
          <h1 className="mt-2 text-3xl font-bold text-[var(--text-primary)]">{team?.name ?? "Team"}</h1>
        </header>

        <form onSubmit={submitMember} className="panel grid gap-3 p-4 sm:grid-cols-[1fr_1fr_auto_auto]">
          <Input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="Member name" required />
          <Input type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} placeholder="member@company.com" required />
          <Button type="submit">{editingId ? "Save" : "Add member"}</Button>
          {editingId && (
            <Button type="button" variant="ghost" onClick={resetForm}>
              Cancel
            </Button>
          )}
        </form>

        <section className="panel overflow-hidden">
          <div className="panel-header flex items-center justify-between">
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">Members</h2>
            <span className="chip">{members.length}</span>
          </div>
          <div className="divide-y divide-[var(--border)]">
            {members.map((member) => {
              const isLead = team?.leader_email === member.email;
              return (
                <div key={member.id} className="flex flex-col justify-between gap-4 px-5 py-4 sm:flex-row sm:items-center">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--primary-soft)] text-xs font-bold text-[var(--primary)]">
                      {member.name.slice(0, 1).toUpperCase()}
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-[var(--text-primary)]">{member.name}</p>
                        {isLead && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700 ring-1 ring-amber-600/20">
                            <svg className="h-3 w-3 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                            Team Lead
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-[var(--text-secondary)]">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex gap-2 items-center">
                    {user?.role === "hr" && !isLead && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => handleAssignLeader(member.id)}
                        className="text-[var(--primary)] border-[var(--primary-soft)] hover:bg-[var(--primary-soft)]"
                      >
                        Make Lead
                      </Button>
                    )}
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setEditingId(member.id);
                        setForm({ name: member.name, email: member.email });
                      }}
                    >
                      Edit
                    </Button>
                    <Button type="button" variant="danger" onClick={() => deleteMember(member.id)}>
                      Delete
                    </Button>
                  </div>
                </div>
              );
            })}
            {!members.length && <div className="px-5 py-12 text-center text-sm text-[var(--text-secondary)]">No members yet.</div>}
          </div>
        </section>
      </div>
    </div>
  );
}
