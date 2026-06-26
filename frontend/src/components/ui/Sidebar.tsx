"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { HelpDrawer } from "./HelpDrawer";
import { CommandPalette } from "./CommandPalette";
import { useEffect, useState } from "react";

type IconName = "dashboard" | "history" | "teams" | "settings" | "plus" | "logout" | "user" | "video";

function Icon({ name, className = "h-4 w-4" }: { name: IconName; className?: string }) {
  const common = {
    fill: "none",
    viewBox: "0 0 24 24",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    className,
  };
  const paths: Record<IconName, React.ReactNode> = {
    dashboard: (
      <>
        <path d="M4 5a1 1 0 0 1 1-1h5v7H4z" />
        <path d="M14 4h5a1 1 0 0 1 1 1v15h-6z" />
        <path d="M4 15h6v5H5a1 1 0 0 1-1-1z" />
      </>
    ),
    history: (
      <>
        <path d="M3 12a9 9 0 1 0 3-6.7" />
        <path d="M3 4v5h5" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    teams: (
      <>
        <path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" />
        <path d="M9.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8" />
        <path d="M22 21v-2a4 4 0 0 0-3-3.9" />
        <path d="M16 3.1a4 4 0 0 1 0 7.8" />
      </>
    ),
    settings: (
      <>
        <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.3 7A2 2 0 1 1 7.1 4.2l.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1A2 2 0 1 1 19.9 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.1a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.7 1" />
      </>
    ),
    plus: (
      <>
        <path d="M12 5v14" />
        <path d="M5 12h14" />
      </>
    ),
    logout: (
      <>
        <path d="M10 17l5-5-5-5" />
        <path d="M15 12H3" />
        <path d="M21 19V5a2 2 0 0 0-2-2h-5" />
      </>
    ),
    user: (
      <>
        <path d="M20 21a8 8 0 0 0-16 0" />
        <path d="M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8" />
      </>
    ),
    video: (
      <>
        <path d="M4 7a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" />
        <path d="m16 10 4-2.5v9L16 14" />
      </>
    ),
  };
  return <svg {...common}>{paths[name]}</svg>;
}

function NavLink({ href, label, icon }: { href: string; label: string; icon: IconName }) {
  const pathname = usePathname();
  const isActive = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));

  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-r-lg px-5 py-2 text-sm font-medium transition-colors ${
        isActive
          ? "border-l-2 border-[var(--primary)] bg-[rgb(245_158_11_/_0.10)] text-[var(--primary)]"
          : "border-l-2 border-transparent text-[var(--text-secondary)] hover:bg-[var(--surface-low)] hover:text-[var(--text-primary)]"
      }`}
    >
      <Icon name={icon} className="h-5 w-5 shrink-0" />
      {label}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const [helpOpen, setHelpOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const isSidebarHidden = pathname === "/" || pathname === "/login" || pathname === "/register" || pathname === "/zoom-meeting";

  useEffect(() => {
    if (isSidebarHidden) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setPaletteOpen((p) => !p);
      }
      if (e.key === "n" && e.altKey) {
        e.preventDefault();
        router.push("/dashboard");
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isSidebarHidden, router]);

  if (isSidebarHidden) return null;

  const navItems = isAuthenticated
    ? [
        { href: "/dashboard", label: "Dashboard", icon: "dashboard" as const },
        { href: "/history", label: "History", icon: "history" as const },
        { href: "/teams", label: "Teams", icon: "teams" as const },

      ]
    : [{ href: "/login", label: "Log in", icon: "user" as const }];

  return (
    <>
      <HelpDrawer open={helpOpen} onClose={() => setHelpOpen(false)} />
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      <aside className="hidden min-h-screen w-[220px] shrink-0 flex-col border-r border-[var(--border)] bg-[var(--surface)] py-6 md:flex">
        <div className="px-6">
          <Link href="/dashboard" className="flex items-center gap-2 text-xl font-bold text-[var(--text-primary)]">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--primary)] text-white">
              <Icon name="video" className="h-4 w-4" />
            </span>
            <span>MeetingAI</span>
          </Link>
          <p className="mt-1 pl-10 text-xs font-medium text-[var(--text-secondary)]">Workspace</p>
        </div>

        <div className="px-4 pt-8">
          <Link
            href="/dashboard"
            className="flex h-8 w-full items-center justify-center gap-2 rounded-lg bg-[var(--primary)] px-4 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)]"
          >
            <Icon name="plus" className="h-4 w-4" />
            New Meeting
          </Link>
        </div>

        <nav className="mt-6 flex flex-1 flex-col gap-1 px-2">
          {navItems.map((item) => (
            <NavLink key={item.href} {...item} />
          ))}
        </nav>

        <div className="mx-4 border-t border-[var(--border)] pt-4">
          {isAuthenticated && user ? (
            <div className="space-y-1">
              <div className="flex items-center gap-3 rounded-lg px-2 py-2">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--primary-soft)] text-xs font-bold text-[var(--primary)]">
                  {user.name.slice(0, 1).toUpperCase()}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-[var(--text-primary)]">{user.name}</p>
                  <p className="truncate text-[11px] text-[var(--text-secondary)]">
                    {user.role === "hr" ? "HR admin" : "Team leader"}
                  </p>
                </div>
              </div>
              <button
                onClick={logout}
                className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-low)] hover:text-[var(--text-primary)]"
              >
                <Icon name="logout" className="h-5 w-5" />
                Logout
              </button>
            </div>
          ) : (
            <Link href="/login" className="block rounded-lg px-2 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-low)]">
              Sign in to continue
            </Link>
          )}
          <button
            onClick={() => setHelpOpen(true)}
            aria-label="Open help and documentation"
            className="mt-2 flex w-full items-center gap-3 rounded-lg px-2 py-2 text-sm font-medium text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-low)] hover:text-[var(--text-primary)]"
          >
            <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.7}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.9 9.9a3 3 0 1 1 4.2 4.2L12 16l-.5-2.5A2 2 0 0 0 10.5 12H9a3 3 0 0 1 .9-2.1" />
              <circle cx="12" cy="12" r="10" />
            </svg>
            Help
          </button>
        </div>
      </aside>
    </>
  );
}
