import Link from "next/link";

const links = [
  { href: "/", label: "Home" },
  { href: "/login", label: "Log in" },
  { href: "/register", label: "Create account" },
];

export function Footer() {
  return (
    <footer className="border-t border-[#d9d7d1] bg-[#f7f7f6] px-6 py-5">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-sm font-bold text-[#171719]">
          <span className="grid h-6 w-6 place-items-center rounded bg-[#171719] text-white">
            <span className="h-2 w-2 rounded-[1px] border border-white" />
          </span>
          MeetingAI
        </Link>
        <nav className="flex gap-4 text-xs font-semibold text-[#5d5a64]">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="transition-colors hover:text-[#171719]"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
