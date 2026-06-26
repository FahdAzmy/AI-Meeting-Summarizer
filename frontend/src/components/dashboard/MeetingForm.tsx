import React, { useEffect, useState, useRef } from 'react';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { detectPlatform, isValidMeetingUrl } from '../../lib/utils';
import { PlatformBadge } from './PlatformBadge';
import { api } from '@/lib/api';
import { CreateMeetingPayload, Member, Team } from '@/lib/types';

const HINT_KEY = "meetingai_url_hint_dismissed";

interface MeetingFormProps {
  onSubmit: (payload: CreateMeetingPayload) => void;
  isLoading?: boolean;
  initialTeams?: Team[];
  initialMembers?: Member[];
}

export function MeetingForm({ onSubmit, isLoading, initialTeams, initialMembers }: MeetingFormProps) {
  const [link, setLink] = useState('');
  const [title, setTitle] = useState('');

  const [teamIds, setTeamIds] = useState<string[]>([]);
  const [memberIds, setMemberIds] = useState<string[]>([]);
  const [teams, setTeams] = useState<Team[]>(() => initialTeams ?? []);
  const [members, setMembers] = useState<Member[]>(() => initialMembers ?? []);
  const [error, setError] = useState('');

  // ── Search & Dropdown States ──────────────────────────────────────────────
  const [teamSearch, setTeamSearch] = useState('');
  const [memberSearch, setMemberSearch] = useState('');
  const [isTeamDropdownOpen, setIsTeamDropdownOpen] = useState(false);
  const [isMemberDropdownOpen, setIsMemberDropdownOpen] = useState(false);
  const [showHint, setShowHint] = useState(true);

  const teamDropdownRef = useRef<HTMLDivElement>(null);
  const memberDropdownRef = useRef<HTMLDivElement>(null);

  const detectedPlatform = detectPlatform(link);

  useEffect(() => {
    const dismissed = localStorage.getItem(HINT_KEY);
    if (dismissed === "true") setShowHint(false);
  }, []);

  const dismissHint = () => {
    setShowHint(false);
    localStorage.setItem(HINT_KEY, "true");
  };

  useEffect(() => {
    let isMounted = true;
    async function loadOptions() {
      try {
        const [teamData, memberData] = await Promise.all([
          initialTeams && initialTeams.length > 0 ? Promise.resolve(initialTeams) : api.getTeams(),
          initialMembers && initialMembers.length > 0 ? Promise.resolve(initialMembers) : api.getMembers(),
        ]);
        if (isMounted) {
          setTeams(teamData);
          setMembers(memberData);
        }
      } catch {
        if (isMounted) {
          setTeams(initialTeams ?? []);
          setMembers(initialMembers ?? []);
        }
      }
    }
    loadOptions();
    return () => {
      isMounted = false;
    };
  }, [initialTeams, initialMembers]);

  // ── Handle outside clicks to close dropdowns ──────────────────────────────
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (teamDropdownRef.current && !teamDropdownRef.current.contains(event.target as Node)) {
        setIsTeamDropdownOpen(false);
      }
      if (memberDropdownRef.current && !memberDropdownRef.current.contains(event.target as Node)) {
        setIsMemberDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ── Sync member selection with team selection ─────────────────────────────
  const pruneMembersForTeams = (nextTeamIds: string[]) => {
    if (nextTeamIds.length === 0) return;
    setMemberIds((prev) =>
      prev.filter((memberId) => {
        const member = members.find((currentMember) => currentMember.id === memberId);
        return member ? nextTeamIds.includes(member.team_id) : false;
      })
    );
  };

  const updateTeamIds = (nextTeamIds: string[]) => {
    setTeamIds(nextTeamIds);
    pruneMembersForTeams(nextTeamIds);
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    const trimmedLink = link.trim();
    if (!trimmedLink) {
      setError('Meeting link is required.');
      return;
    }
    if (!isValidMeetingUrl(trimmedLink)) {
      const platform = detectPlatform(trimmedLink);
      setError(platform ? 'Invalid meeting URL format for this platform.' : 'Unsupported platform. Use Google Meet, Zoom, or Microsoft Teams.');
      return;
    }
    onSubmit({
      meeting_link: trimmedLink,
      title: title.trim() || undefined,
      team_ids: teamIds,
      member_ids: memberIds,
    });
  };

  // ── Filtered Choices ──────────────────────────────────────────────────────
  const filteredTeams = teams.filter((team) =>
    team.name.toLowerCase().includes(teamSearch.toLowerCase())
  );

  const filteredMembers = members.filter((member) => {
    // If teams are selected, only show members of those teams
    if (teamIds.length > 0 && !teamIds.includes(member.team_id)) {
      return false;
    }
    return (
      member.name.toLowerCase().includes(memberSearch.toLowerCase()) ||
      member.email.toLowerCase().includes(memberSearch.toLowerCase())
    );
  });

  return (
    <form
      onSubmit={handleSubmit}
      className="panel relative"
    >
      <div className="panel-header rounded-t-xl">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--surface)] text-[var(--primary)] ring-1 ring-[var(--border)]">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.8 10.2a4 4 0 0 0-5.6 0l-4 4a4 4 0 0 0 5.6 5.6l1.1-1.1" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.2 13.8a4 4 0 0 0 5.6 0l4-4a4 4 0 0 0-5.6-5.6l-1.1 1.1" />
            </svg>
          </div>
          <div>
            <h2 className="text-sm font-semibold text-[var(--text-primary)] leading-none">Schedule meeting</h2>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">Select teams or individual participants.</p>
          </div>
        </div>
      </div>

      <div className="px-6 py-5 space-y-4">
        <div className="space-y-1.5">
          <label className="label-caps">Meeting URL</label>
          <div className={`flex gap-2 items-center ${showHint && !link ? "hint-pulse" : ""}`}>
            <Input
              type="url"
              placeholder="https://meet.google.com/abc-defg-hij"
              value={link}
              onChange={(event) => { setLink(event.target.value); dismissHint(); }}
              onFocus={dismissHint}
              maxLength={2048}
              aria-describedby={error ? "url-error" : undefined}
              aria-invalid={!!error}
            />
            {detectedPlatform && <PlatformBadge platform={detectedPlatform} />}
          </div>
            {error && <p id="url-error" role="alert" className="rounded-lg border border-[var(--danger)]/20 bg-[var(--danger)]/5 px-3 py-2 text-xs text-[var(--danger)]">{error}</p>}
        </div>

        <div className="space-y-1.5">
          <label className="label-caps">Title</label>
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Sprint Planning" maxLength={200} />
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          {/* Teams Selector */}
          <div className="space-y-1.5 relative" ref={teamDropdownRef}>
            <label className="label-caps">Teams</label>
            <div 
              className="flex flex-wrap gap-1.5 p-2 min-h-10 w-full rounded-lg border border-transparent bg-[var(--surface-recessed)] focus-within:border-[var(--primary)]               focus-within:bg-[var(--surface)] focus-within:ring-2 focus-within:ring-[rgb(245_158_11_/_20%)] transition-all cursor-text"
              onClick={() => setIsTeamDropdownOpen(true)}
            >
              {teamIds.map((id) => {
                const team = teams.find((t) => t.id === id);
                if (!team) return null;
                return (
                  <span key={team.id} className="inline-flex items-center gap-1 rounded bg-[var(--primary-soft)] px-2 py-0.5 text-xs font-medium text-[var(--primary)] animate-fade-up">
                    {team.name}
                    <button
                      type="button"
                      aria-label={`Remove ${team.name}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        updateTeamIds(teamIds.filter((teamId) => teamId !== id));
                      }}
                      className="hover:text-[var(--danger)] transition-colors"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </span>
                );
              })}
              <input
                type="text"
                aria-label="Search teams"
                value={teamSearch}
                onChange={(e) => {
                  setTeamSearch(e.target.value);
                  setIsTeamDropdownOpen(true);
                }}
                onFocus={() => setIsTeamDropdownOpen(true)}
                placeholder={teamIds.length === 0 ? "Select teams..." : ""}
                className="flex-1 min-w-[100px] bg-transparent text-sm text-[var(--text-primary)] outline-none border-none placeholder:text-[var(--text-muted)] p-0"
              />
            </div>
            
            {isTeamDropdownOpen && (
              <div className="absolute left-0 right-0 mt-1 max-h-56 overflow-y-auto rounded-lg border border-[var(--border)] bg-[var(--surface)] py-1 shadow-lg z-50 animate-fade-up">
                {filteredTeams.length === 0 ? (
                  <p className="px-3 py-2 text-xs text-[var(--text-muted)]">No teams found</p>
                ) : (
                  filteredTeams.map((team) => {
                    const isSelected = teamIds.includes(team.id);
                    return (
                      <button
                        key={team.id}
                        type="button"
                        onClick={() => {
                          if (isSelected) {
                            updateTeamIds(teamIds.filter((teamId) => teamId !== team.id));
                          } else {
                            updateTeamIds([...teamIds, team.id]);
                          }
                        }}
                        className={`flex items-center justify-between w-full px-3 py-2 text-left text-sm transition-colors hover:bg-[var(--surface-low)] ${
                          isSelected ? 'bg-[var(--primary-soft)]/20 font-medium text-[var(--primary)]' : 'text-[var(--text-primary)]'
                        }`}
                      >
                        <span>{team.name}</span>
                        {isSelected && (
                          <svg className="h-4 w-4 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>

          {/* Members Selector */}
          <div className="space-y-1.5 relative" ref={memberDropdownRef}>
            <label className="label-caps">Members</label>
            <div 
              className="flex flex-wrap gap-1.5 p-2 min-h-10 w-full rounded-lg border border-transparent bg-[var(--surface-recessed)] focus-within:border-[var(--primary)]               focus-within:bg-[var(--surface)] focus-within:ring-2 focus-within:ring-[rgb(245_158_11_/_20%)] transition-all cursor-text"
              onClick={() => setIsMemberDropdownOpen(true)}
            >
              {memberIds.map((id) => {
                const member = members.find((m) => m.id === id);
                if (!member) return null;
                return (
                  <span key={member.id} className="inline-flex items-center gap-1 rounded bg-[var(--primary-soft)] px-2 py-0.5 text-xs font-medium text-[var(--primary)] animate-fade-up">
                    {member.name}
                    <button
                      type="button"
                      aria-label={`Remove ${member.name}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setMemberIds(memberIds.filter((mId) => mId !== id));
                      }}
                      className="hover:text-[var(--danger)] transition-colors"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </span>
                );
              })}
              <input
                type="text"
                aria-label="Search members"
                value={memberSearch}
                onChange={(e) => {
                  setMemberSearch(e.target.value);
                  setIsMemberDropdownOpen(true);
                }}
                onFocus={() => setIsMemberDropdownOpen(true)}
                placeholder={memberIds.length === 0 ? "Select members..." : ""}
                className="flex-1 min-w-[100px] bg-transparent text-sm text-[var(--text-primary)] outline-none border-none placeholder:text-[var(--text-muted)] p-0"
              />
            </div>
            
            {isMemberDropdownOpen && (
              <div className="absolute left-0 right-0 mt-1 max-h-56 overflow-y-auto rounded-lg border border-[var(--border)] bg-[var(--surface)] py-1 shadow-lg z-50 animate-fade-up">
                {filteredMembers.length === 0 ? (
                  <p className="px-3 py-2 text-xs text-[var(--text-muted)]">No members found</p>
                ) : (
                  filteredMembers.map((member) => {
                    const isSelected = memberIds.includes(member.id);
                    return (
                      <button
                        key={member.id}
                        type="button"
                        onClick={() => {
                          if (isSelected) {
                            setMemberIds(memberIds.filter((id) => id !== member.id));
                          } else {
                            setMemberIds([...memberIds, member.id]);
                          }
                        }}
                        className={`flex items-center justify-between w-full px-3 py-2 text-left text-sm transition-colors hover:bg-[var(--surface-low)] ${
                          isSelected ? 'bg-[var(--primary-soft)]/20 font-medium text-[var(--primary)]' : 'text-[var(--text-primary)]'
                        }`}
                      >
                        <div className="flex flex-col">
                          <span className="font-medium">{member.name}</span>
                          <span className="text-xs text-[var(--text-muted)]">{member.email}</span>
                        </div>
                        {isSelected && (
                          <svg className="h-4 w-4 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end border-t border-[var(--border)] bg-[var(--surface-recessed)] px-6 py-4 rounded-b-xl">
        <Button type="submit" disabled={isLoading || !link} className="shrink-0">
          {isLoading ? "Starting..." : "Start session"}
        </Button>
      </div>
    </form>
  );
}
