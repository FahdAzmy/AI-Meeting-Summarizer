import * as React from "react"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'danger' | 'ghost';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "default", ...props }, ref) => {
    const base = "inline-flex h-8 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(245_158_11_/_0.25)] disabled:pointer-events-none disabled:opacity-45";
    const variants = {
      default: "bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)]",
      outline: "border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] hover:bg-[var(--surface-low)]",
      danger:  "bg-[var(--danger)] text-white hover:bg-red-700",
      ghost:   "text-[var(--text-secondary)] hover:bg-[var(--surface-low)] hover:text-[var(--text-primary)]",
    };
    return (
      <button
        className={`${base} ${variants[variant]} ${className}`}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"
