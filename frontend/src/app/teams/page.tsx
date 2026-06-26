"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Team, UserRole } from "@/lib/types";

interface TeamsPageProps {
  initialTeams?: Team[];
  userRole?: UserRole;
}

export default function TeamsPage({ initialTeams, userRole }: TeamsPageProps) {
  const { user, isAuthenticated, isReady } = useAuth();
  const [teams, setTeams] = useState<Team[]>(initialTeams ?? []);
  const [name, setName] = useState("");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(!initialTeams);
  const role = userRole ?? user?.role;
  const canCreate = role === "hr";

  useEffect(() => {
    let isMounted = true;
    async function loadTeams() {
      if (initialTeams || !isAuthenticated) return;
      try {
        setIsLoading(true);
        const data = await api.getTeams();
        if (isMounted) setTeams(data);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    loadTeams();
    return () => {
      isMounted = false;
    };
  }, [initialTeams, isAuthenticated]);

  const createTeam = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    try {
      const team = await api.createTeam(name.trim());
      setTeams((current) => [...current, team]);
      setName("");
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = useMemo(
    () => teams.filter((team) => !search || team.name.toLowerCase().includes(search.toLowerCase())),
    [teams, search],
  );

  if (!initialTeams && (!isReady || !isAuthenticated)) {
    return <div className="p-8 text-sm text-[var(--text-secondary)]">Loading workspace...</div>;
  }

  return (
    <div className="page-canvas animate-fade-up">
      <div className="space-y-6">
        <header className="flex flex-col justify-between gap-4 border-b border-[var(--border)] pb-6 lg:flex-row lg:items-center">
          <div>
            <h1 className="text-3xl font-bold text-[var(--text-primary)]">Teams</h1>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">Manage team ownership and meeting participation.</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative">
              <svg className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-4.3-4.3m1.3-5.2a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0" />
              </svg>
              <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search teams..." className="pl-9 sm:w-64" />
            </div>
            {canCreate && (
              <form onSubmit={createTeam} className="flex gap-2">
                <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Team name" className="sm:w-48" maxLength={100} />
                <Button type="submit" variant="outline">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14M5 12h14" />
                  </svg>
                  Create Team
                </Button>
              </form>
            )}
          </div>
        </header>

        {isLoading ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="panel h-40 animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          teams.length === 0 ? (
            <div className="panel px-6 py-16 text-center">
              <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--surface-recessed)] text-[var(--text-muted)]">
                <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M22 21v-2a4 4 0 0 0-3-3.9" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 3.1a4 4 0 0 1 0 7.8" />
                </svg>
              </div>
              <h3 className="text-base font-semibold text-[var(--text-primary)]">No teams yet</h3>
              <p className="mx-auto mt-2 max-w-xs text-sm text-[var(--text-secondary)]">
                Teams group members together for meeting participation and reporting. Create your first team to get started.
              </p>
              {canCreate && (
                <button
                  onClick={() => {
                    const input = document.querySelector<HTMLInputElement>('input[placeholder="Team name"]');
                    input?.focus();
                  }}
                  className="mt-6 inline-flex h-8 items-center gap-2 rounded-lg bg-[var(--primary)] px-4 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)]"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14M5 12h14" />
                  </svg>
                  Create your first team
                </button>
              )}
            </div>
          ) : (
            <div className="panel px-6 py-16 text-center text-sm text-[var(--text-secondary)]">No teams match "{search}".</div>
          )
        ) : (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map((team) => (
              <Link key={team.id} href={`/teams/${team.id}`} className="panel group flex min-h-40 flex-col gap-4 p-5 transition-colors hover:border-[var(--primary)]">
                <div className="flex items-start justify-between">
                  <h2 className="truncate text-[15px] font-semibold text-[var(--text-primary)]">{team.name}</h2>
                  <span className="flex items-center gap-1 text-xs font-medium text-[var(--primary)] opacity-0 transition-opacity group-hover:opacity-100">
                    Manage
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="m9 5 7 7-7 7" />
                    </svg>
                  </span>
                </div>
                <div className="flex items-center gap-3 border-b border-[var(--border)] pb-4">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--primary-soft)] text-xs font-bold text-[var(--primary)]">
                    {team.name.slice(0, 1).toUpperCase()}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-[var(--text-primary)]">{team.leader_id ? "Leader assigned" : "No leader assigned"}</p>
                    <p className="mt-0.5 flex items-center gap-1 text-[11px] text-[var(--text-secondary)]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[var(--ai-accent)]" />
                      Lead
                    </p>
                  </div>
                </div>
                <div className="mt-auto flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs font-medium text-[var(--text-secondary)]">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2M9.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8" />
                    </svg>
                    {team.members_count ?? 0} members
                  </span>
                  <div className="flex -space-x-2">
                    {Array.from({ length: Math.min(team.members_count ?? 0, 4) }).map((_, index) => (
                      <span key={index} className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[var(--surface-recessed)] text-[10px] font-medium text-[var(--text-secondary)] ring-2 ring-white">
                        {index + 1}
                      </span>
                    ))}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
