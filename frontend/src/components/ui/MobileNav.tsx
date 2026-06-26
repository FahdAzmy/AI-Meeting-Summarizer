"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

type IconName = "dashboard" | "history" | "teams";

function Icon({ name, className = "h-5 w-5" }: { name: IconName; className?: string }) {
  const svgProps = { fill: "none" as const, viewBox: "0 0 24 24", stroke: "currentColor" as const, strokeWidth: 1.7, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, className };
  const paths: Record<IconName, React.ReactNode> = {
    dashboard: <><path d="M4 5a1 1 0 0 1 1-1h5v7H4z" /><path d="M14 4h5a1 1 0 0 1 1 1v15h-6z" /><path d="M4 15h6v5H5a1 1 0 0 1-1-1z" /></>,
    history: <><path d="M3 12a9 9 0 1 0 3-6.7" /><path d="M3 4v5h5" /><path d="M12 7v5l3 2" /></>,
    teams: <><path d="M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2" /><path d="M9.5 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8" /><path d="M22 21v-2a4 4 0 0 0-3-3.9" /><path d="M16 3.1a4 4 0 0 1 0 7.8" /></>,
  };
  return <svg {...svgProps}>{paths[name]}</svg>;
}

const navItems: { href: string; label: string; icon: IconName }[] = [
  { href: "/dashboard", label: "Home", icon: "dashboard" },
  { href: "/history", label: "History", icon: "history" },
  { href: "/teams", label: "Teams", icon: "teams" },

];

export function MobileNav() {
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();

  if (pathname === "/login" || pathname === "/register" || pathname === "/zoom-meeting" || pathname === "/") return null;

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-30 flex items-center justify-around border-t border-[var(--border)] bg-[var(--surface)] px-2 pb-[max(0px,env(safe-area-inset-bottom))] md:hidden"
      role="navigation"
      aria-label="Mobile navigation"
    >
      {navItems.map((item) => {
        const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center gap-0.5 px-3 py-2 text-[10px] font-medium transition-colors ${
              isActive
                ? "text-[var(--primary)]"
                : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
            }`}
          >
            <Icon name={item.icon} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
