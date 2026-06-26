import Image from "next/image";
import Link from "next/link";

const workflow = [
  {
    step: "01",
    title: "Paste the room",
    body: "Start from a Google Meet, Zoom, or Teams link and assign teams or individual participants.",
  },
  {
    step: "02",
    title: "Let the pipeline run",
    body: "The bot joins, records system audio, transcribes, summarizes, and tracks every stage.",
  },
  {
    step: "03",
    title: "Ship the record",
    body: "Structured summaries, action items, decisions, and transcripts become searchable deliverables.",
  },
];

const capabilities = [
  "Participant-aware routing",
  "Team and HR workspaces",
  "Searchable meeting history",
  "Action item extraction",
  "Export-ready summaries",
  "Provider-flexible STT",
];

const stats = [
  { value: "5", label: "pipeline stages" },
  { value: "3", label: "meeting platforms" },
  { value: "0", label: "manual note passes" },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#0b0d14] text-[#f8fafc]">
      <header className="relative z-20 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <Link href="/" className="flex items-center gap-3 font-bold text-[#f8fafc]">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-[#f59e0b] text-[#0b0d14]">
            <span className="h-3 w-3 rounded-[2px] border border-[#0b0d14]" />
          </span>
          <span>MeetingAI</span>
        </Link>
        <nav className="flex items-center gap-2 text-sm font-semibold">
          <Link href="/login" className="rounded-md px-3 py-2 text-[#94a3b8] transition-colors hover:text-[#f8fafc]">
            Log in
          </Link>
          <Link href="/register" className="rounded-md bg-[#f59e0b] px-4 py-2 text-[#0b0d14] transition-colors hover:bg-[#d97706]">
            Create workspace
          </Link>
        </nav>
      </header>

      <section className="relative -mt-20 flex min-h-[90svh] overflow-hidden pt-20">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_30%_20%,rgba(245,158,11,0.08)_0%,transparent_60%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_70%_80%,rgba(59,130,246,0.06)_0%,transparent_50%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:56px_56px]" />

        <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 items-center px-5 pb-16 sm:px-8">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#f59e0b]/20 bg-[#f59e0b]/5 px-4 py-1.5 text-xs font-semibold text-[#f59e0b]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#f59e0b] animate-pulse" />
              Autonomous meeting documentation
            </div>
            <h1 className="mt-6 max-w-4xl text-5xl font-black leading-[0.92] tracking-tight sm:text-7xl lg:text-8xl">
              Meetings document
              <br />
              <span className="text-[#f59e0b]">themselves.</span>
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-7 text-[#8892a4] sm:text-lg">
              A command center that joins meetings, captures audio, turns conversations into structured records, and keeps teams accountable without another manual notes pass.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/register" className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-[#f59e0b] px-7 text-sm font-bold text-[#0b0d14] transition-all hover:bg-[#d97706] hover:shadow-[0_0_30px_-5px_rgba(245,158,11,0.4)]">
                Start your workspace
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                </svg>
              </Link>
              <Link href="/login" className="inline-flex h-12 items-center justify-center rounded-lg border border-[#1e2740] px-7 text-sm font-bold text-[#f8fafc] transition-colors hover:border-[#3b475c] hover:bg-[#111624]">
                Open dashboard
              </Link>
            </div>

            <dl className="mt-14 flex gap-8 border-t border-[#1e2740] pt-6">
              {stats.map((stat) => (
                <div key={stat.label}>
                  <dt className="text-3xl font-black tracking-tight text-[#f8fafc]">{stat.value}</dt>
                  <dd className="mt-1 text-xs font-semibold uppercase tracking-wider text-[#64748b]">{stat.label}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      <section className="border-t border-[#1e2740] px-5 py-24 sm:px-8">
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-[#f59e0b]">Operating model</p>
            <h2 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">
              One pipeline from live conversation to accountable record.
            </h2>
          </div>
          <div className="grid gap-4">
            {workflow.map((item) => (
              <article key={item.step} className="group relative overflow-hidden rounded-lg border border-[#1e2740] bg-[#111624] p-6 transition-colors hover:border-[#2a3a5c] sm:grid sm:grid-cols-[64px_1fr] sm:gap-5">
                <span className="relative z-10 text-3xl font-black text-[#f59e0b]">{item.step}</span>
                <div className="relative z-10">
                  <h3 className="text-lg font-bold">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#8892a4]">{item.body}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-[#1e2740] bg-[#0d1220] px-5 py-24 sm:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-4 md:grid-cols-3">
            <figure className="overflow-hidden rounded-lg border border-[#1e2740] bg-[#111624] md:col-span-2">
              <div className="relative aspect-[16/9]">
                <Image src="/landing/history.png" alt="MeetingAI history table" fill sizes="(min-width: 768px) 66vw, 100vw" className="object-cover opacity-90" />
              </div>
              <figcaption className="border-t border-[#1e2740] px-5 py-4 text-sm font-medium text-[#94a3b8]">
                Every completed meeting becomes a searchable operational record.
              </figcaption>
            </figure>
            <div className="grid gap-3">
              {capabilities.map((capability) => (
                <div key={capability} className="flex items-center gap-3 rounded-lg border border-[#1e2740] bg-[#111624] px-5 py-4 text-sm font-semibold text-[#f8fafc] transition-colors hover:border-[#2a3a5c]">
                  <svg className="h-4 w-4 shrink-0 text-[#f59e0b]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  {capability}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
            <div className="relative overflow-hidden rounded-lg border border-[#f59e0b]/10 bg-gradient-to-br from-[#0b0d14] via-[#111624] to-[#1a1f2e] p-8">
              <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-[#f59e0b]/5 blur-3xl" />
              <p className="relative text-xs font-bold uppercase tracking-widest text-[#f59e0b]">Built for managers</p>
              <h2 className="relative mt-4 text-3xl font-black leading-tight">
                Less ceremony. More proof of what was decided.
              </h2>
              <p className="relative mt-4 max-w-sm text-sm leading-6 text-[#8892a4]">
                HR admins see company-wide participation. Team leaders keep member context close. Everyone gets the same consistent meeting record.
              </p>
            </div>
            <figure className="overflow-hidden rounded-lg border border-[#1e2740] bg-[#111624]">
              <div className="relative aspect-[16/9]">
                <Image src="/landing/teams.png" alt="MeetingAI team management workspace" fill sizes="(min-width: 1024px) 60vw, 100vw" className="object-cover opacity-90" />
              </div>
            </figure>
          </div>
        </div>
      </section>

      <section className="border-t border-[#1e2740] px-5 py-24 sm:px-8">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-8 lg:flex-row lg:items-center">
          <div className="max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-widest text-[#f59e0b]">Ready when the next call starts</p>
            <h2 className="mt-4 text-4xl font-black leading-tight">
              Turn the next meeting into a finished record.
            </h2>
          </div>
          <Link href="/register" className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-lg bg-[#f59e0b] px-7 text-sm font-bold text-[#0b0d14] transition-all hover:bg-[#d97706] hover:shadow-[0_0_30px_-5px_rgba(245,158,11,0.4)]">
            Create workspace
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </div>
      </section>
    </main>
  );
}
