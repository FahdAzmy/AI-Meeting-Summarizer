"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/lib/auth";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginPage({ onSubmit }: any = {}) {
  const { login, isReady, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isReady && isAuthenticated) router.replace("/dashboard");
  }, [isReady, isAuthenticated, router]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  const validate = () => {
    const errors: { email?: string; password?: string } = {};
    const trimmedEmail = email.trim();
    if (!trimmedEmail) errors.email = "Email is required.";
    else if (!EMAIL_RE.test(trimmedEmail)) errors.email = "Enter a valid email address.";
    if (!password) errors.password = "Password is required.";
    else if (password.length < 6) errors.password = "Password must be at least 6 characters.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    if (!validate()) return;
    setIsLoading(true);
    try {
      if (onSubmit) {
        await onSubmit(email.trim(), password);
      } else {
        await login({ email: email.trim(), password });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#0b0d14]">
      <div className="flex flex-1">
        <div className="relative hidden w-[45%] flex-col overflow-hidden lg:flex">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_30%_20%,rgba(245,158,11,0.1)_0%,transparent_60%)]" />
          <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:56px_56px]" />

          <div className="relative z-10 flex flex-1 flex-col p-12">
            <div className="flex items-center gap-3 font-bold text-[#f8fafc]">
              <span className="grid h-9 w-9 place-items-center rounded-md bg-[#f59e0b] text-[#0b0d14]">
                <span className="h-3 w-3 rounded-[2px] border border-[#0b0d14]" />
              </span>
              <span>MeetingAI</span>
            </div>

            <div className="mt-auto">
              <p className="text-xs font-bold uppercase tracking-wider text-[#f59e0b]">
                Autonomous meeting documentation
              </p>
              <h2 className="mt-4 text-4xl font-black leading-[0.95] text-[#f8fafc]">
                Sign back in.
                <br />
                Pick up where you left off.
              </h2>
              <p className="mt-4 max-w-sm text-sm leading-6 text-[#8892a4]">
                Your workspace keeps everything organized across teams, meetings, and action items.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-center bg-[#111624] px-6 py-12">
          <div className="w-full max-w-sm">
            <div className="mb-8">
              <p className="text-xs font-bold uppercase tracking-wider text-[#f59e0b]">Welcome back</p>
              <h1 className="mt-3 text-4xl font-black leading-[0.95] text-[#f8fafc]">Log in</h1>
              <p className="mt-3 text-sm leading-6 text-[#8892a4]">
                Access your workspace and continue where you left off.
              </p>
            </div>

            <form onSubmit={handleSubmit} noValidate className="space-y-5">
              <div className="space-y-2">
                <label
                  htmlFor="email"
                  className="text-xs font-semibold uppercase tracking-wider text-[#94a3b8]"
                >
                  Email
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    setFieldErrors((prev) => ({ ...prev, email: undefined }));
                  }}
                  required
                  maxLength={254}
                  aria-describedby={fieldErrors.email ? "email-error" : undefined}
                  aria-invalid={!!fieldErrors.email}
                  className="border-[#1e2740] bg-[#111624] text-[#f8fafc] placeholder:text-[#64748b] hover:bg-[#111624] focus:border-[#f59e0b]/40"
                />
                {fieldErrors.email && (
                  <p id="email-error" role="alert" className="text-xs text-[#ef4444]">
                    {fieldErrors.email}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <label
                  htmlFor="password"
                  className="text-xs font-semibold uppercase tracking-wider text-[#94a3b8]"
                >
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value);
                    setFieldErrors((prev) => ({ ...prev, password: undefined }));
                  }}
                  required
                  minLength={6}
                  maxLength={128}
                  aria-describedby={fieldErrors.password ? "password-error" : undefined}
                  aria-invalid={!!fieldErrors.password}
                  className="border-[#1e2740] bg-[#111624] text-[#f8fafc] placeholder:text-[#64748b] hover:bg-[#111624] focus:border-[#f59e0b]/40"
                />
                {fieldErrors.password && (
                  <p id="password-error" role="alert" className="text-xs text-[#ef4444]">
                    {fieldErrors.password}
                  </p>
                )}
              </div>

              {error && (
                <p role="alert" className="rounded-lg border border-[#ef4444]/20 bg-[#ef4444]/5 px-3 py-2 text-sm text-[#ef4444]">
                  {error}
                </p>
              )}

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full h-10 bg-[#f59e0b] text-[#0b0d14] hover:bg-[#d97706]"
              >
                {isLoading ? "Logging in..." : "Log in"}
              </Button>

              <p className="text-center text-sm text-[#64748b]">
                New workspace?{" "}
                <Link
                  href="/register"
                  className="font-semibold text-[#f59e0b] transition-colors hover:text-[#d97706]"
                >
                  Create account
                </Link>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
