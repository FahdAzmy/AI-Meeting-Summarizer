"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/lib/auth";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function RegisterPage() {
  const { register, isReady, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isReady && isAuthenticated) router.replace("/dashboard");
  }, [isReady, isAuthenticated, router]);

  const [form, setForm] = useState({ name: "", email: "", password: "", company_name: "", confirmPassword: "" });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const update = (key: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
    setFieldErrors((prev) => ({ ...prev, [key]: "" }));
    if (key === "password" && form.confirmPassword) {
      if (value !== form.confirmPassword) {
        setFieldErrors((prev) => ({ ...prev, confirmPassword: "Passwords do not match." }));
      } else {
        setFieldErrors((prev) => ({ ...prev, confirmPassword: "" }));
      }
    }
    if (key === "confirmPassword" && form.password) {
      if (value !== form.password) {
        setFieldErrors((prev) => ({ ...prev, confirmPassword: "Passwords do not match." }));
      } else {
        setFieldErrors((prev) => ({ ...prev, confirmPassword: "" }));
      }
    }
  };

  const validate = () => {
    const errors: Record<string, string> = {};
    if (!form.name.trim()) errors.name = "Name is required.";
    if (!form.company_name.trim()) errors.company_name = "Company is required.";
    if (!form.email.trim()) errors.email = "Email is required.";
    else if (!EMAIL_RE.test(form.email.trim())) errors.email = "Enter a valid email address.";
    if (!form.password) errors.password = "Password is required.";
    else if (form.password.length < 6) errors.password = "Password must be at least 6 characters.";
    if (!form.confirmPassword) errors.confirmPassword = "Please confirm your password.";
    else if (form.password !== form.confirmPassword) errors.confirmPassword = "Passwords do not match.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    if (!validate()) return;
    setIsLoading(true);
    try {
      await register({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        company_name: form.company_name.trim(),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
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
                Start your workspace
              </p>
              <h2 className="mt-4 text-4xl font-black leading-[0.95] text-[#f8fafc]">
                Turn meetings into
                <br />
                finished records.
              </h2>
              <p className="mt-4 max-w-sm text-sm leading-6 text-[#8892a4]">
                Join meetings, capture audio, and get structured summaries—without a single manual note.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-1 items-center justify-center bg-[#111624] px-6 py-12">
          <div className="w-full max-w-sm">
            <div className="mb-8">
              <p className="text-xs font-bold uppercase tracking-wider text-[#f59e0b]">Get started</p>
              <h1 className="mt-3 text-4xl font-black leading-[0.95] text-[#f8fafc]">Create account</h1>
              <p className="mt-3 text-sm leading-6 text-[#8892a4]">
                Set up your workspace and start documenting meetings instantly.
              </p>
            </div>

            <form onSubmit={handleSubmit} noValidate className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <label
                    htmlFor="name"
                    className="text-xs font-semibold uppercase tracking-wider text-[#94a3b8]"
                  >
                    Name
                  </label>
                  <Input
                    id="name"
                    placeholder="Your name"
                    value={form.name}
                    onChange={(event) => update("name", event.target.value)}
                    required
                    maxLength={100}
                    aria-describedby={fieldErrors.name ? "name-error" : undefined}
                    aria-invalid={!!fieldErrors.name}
                    className="border-[#1e2740] bg-[#111624] text-[#f8fafc] placeholder:text-[#64748b] hover:bg-[#111624] focus:border-[#f59e0b]/40"
                  />
                  {fieldErrors.name && (
                    <p id="name-error" role="alert" className="text-xs text-[#ef4444]">
                      {fieldErrors.name}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <label
                    htmlFor="company"
                    className="text-xs font-semibold uppercase tracking-wider text-[#94a3b8]"
                  >
                    Company
                  </label>
                  <Input
                    id="company"
                    placeholder="Company name"
                    value={form.company_name}
                    onChange={(event) => update("company_name", event.target.value)}
                    required
                    maxLength={100}
                    aria-describedby={fieldErrors.company_name ? "company-error" : undefined}
                    aria-invalid={!!fieldErrors.company_name}
                    className="border-[#1e2740] bg-[#111624] text-[#f8fafc] placeholder:text-[#64748b] hover:bg-[#111624] focus:border-[#f59e0b]/40"
                  />
                  {fieldErrors.company_name && (
                    <p id="company-error" role="alert" className="text-xs text-[#ef4444]">
                      {fieldErrors.company_name}
                    </p>
                  )}
                </div>
              </div>

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
                  value={form.email}
                  onChange={(event) => update("email", event.target.value)}
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
                  placeholder="Min. 6 characters"
                  value={form.password}
                  onChange={(event) => update("password", event.target.value)}
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

              <div className="space-y-2">
                <label
                  htmlFor="confirmPassword"
                  className="text-xs font-semibold uppercase tracking-wider text-[#94a3b8]"
                >
                  Confirm password
                </label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Re-enter your password"
                  value={form.confirmPassword}
                  onChange={(event) => update("confirmPassword", event.target.value)}
                  required
                  maxLength={128}
                  aria-describedby={fieldErrors.confirmPassword ? "confirm-password-error" : undefined}
                  aria-invalid={!!fieldErrors.confirmPassword}
                  className="border-[#1e2740] bg-[#111624] text-[#f8fafc] placeholder:text-[#64748b] hover:bg-[#111624] focus:border-[#f59e0b]/40"
                />
                {fieldErrors.confirmPassword && (
                  <p id="confirm-password-error" role="alert" className="text-xs text-[#ef4444]">
                    {fieldErrors.confirmPassword}
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
                {isLoading ? "Creating workspace..." : "Create account"}
              </Button>

              <p className="text-center text-sm text-[#64748b]">
                Already registered?{" "}
                <Link
                  href="/login"
                  className="font-semibold text-[#f59e0b] transition-colors hover:text-[#d97706]"
                >
                  Log in
                </Link>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
