import * as React from "react"

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={`focus-ring flex h-9 w-full rounded-lg border border-transparent bg-[var(--surface-recessed)] px-3.5 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] transition-colors hover:bg-[var(--surface)] disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"
