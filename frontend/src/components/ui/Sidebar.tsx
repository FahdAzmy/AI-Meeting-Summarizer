"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  {
    href: "/",
    label: "Dashboard",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    href: "/history",
    label: "History",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

function NavLink({ href, label, icon }: { href: string; label: string; icon: React.ReactNode }) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={`relative flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-150 group ${
        isActive
          ? "bg-stone-900 text-white shadow-sm"
          : "text-stone-500 hover:text-stone-900 hover:bg-stone-100"
      }`}
    >
      <span className={`transition-colors ${isActive ? "text-white" : "text-stone-400 group-hover:text-stone-700"}`}>
        {icon}
      </span>
      {label}
      {isActive && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-white/60" />}
    </Link>
  );
}

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 bg-white border-r border-stone-200 flex flex-col min-h-screen">
      {/* Logo */}
      <div className="h-14 flex items-center px-5 border-b border-stone-100">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-xl bg-stone-900 flex items-center justify-center shadow-sm">
            <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <div>
            <span className="font-heading font-bold text-stone-900 text-sm block leading-none">MeetingAI</span>
            <span className="text-[10px] text-stone-400 font-medium">Workspace</span>
          </div>
        </div>
      </div>

      {/* Main nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="text-[10px] font-bold text-stone-400 uppercase tracking-widest px-3 pb-2">Pages</p>
        {navItems.map((item) => (
          <NavLink key={item.href} {...item} />
        ))}
      </nav>

      {/* Settings */}
      <div className="px-3 pt-2 pb-3 border-t border-stone-100 space-y-1">
        <NavLink
          href="/settings"
          label="Settings"
          icon={
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
        />
      </div>

      {/* User card */}
      <div className="px-3 pb-4 pt-1">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-stone-50 border border-stone-100">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-stone-400 to-stone-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
            U
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-stone-800 truncate leading-none">User</p>
            <p className="text-[10px] text-stone-400 truncate mt-0.5">Free plan</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
