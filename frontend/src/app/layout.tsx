import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { ToastProvider } from "@/components/ui/Toast";
import { Sidebar } from "@/components/ui/Sidebar";
import { MobileNav } from "@/components/ui/MobileNav";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "AI Meeting Assistant",
  description: "Summarize and analyze meetings instantly with AI.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans min-h-screen">
        <ToastProvider>
          <AuthProvider>
            <div className="workspace-shell flex">
              <Sidebar />
              <main className="min-w-0 flex-1">
                {children}
              </main>
              <MobileNav />
            </div>
          </AuthProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
