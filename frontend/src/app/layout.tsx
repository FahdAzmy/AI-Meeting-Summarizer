import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Outfit } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/Toast";
import { Sidebar } from "@/components/ui/Sidebar";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "AI Meeting Assistant",
  description: "Summarize and analyze meetings instantly with AI.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${jakarta.variable} ${outfit.variable} font-sans min-h-screen flex`}>
        <ToastProvider>
          <Sidebar />
          <div className="flex-1 flex flex-col min-h-screen overflow-hidden dot-grid">
            {/* Sticky top bar */}
            <header className="h-14 bg-white/80 backdrop-blur-md border-b border-stone-200 flex items-center px-8 shrink-0 sticky top-0 z-10">
              <div className="flex-1" />
              <div className="flex items-center gap-2 text-xs text-stone-400">
                <span className="hidden sm:block font-medium text-stone-500">AI Meeting Assistant</span>
                <span className="w-1 h-1 rounded-full bg-stone-300 hidden sm:block" />
                <span className="font-semibold text-emerald-600 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
                  Online
                </span>
              </div>
            </header>
            <main className="flex-1 overflow-auto">
              {children}
            </main>
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}
