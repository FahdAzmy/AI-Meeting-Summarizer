import * as React from "react"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'danger' | 'ghost';
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "default", ...props }, ref) => {
    const base = "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/20 disabled:pointer-events-none disabled:opacity-40 h-10 px-4 py-2 active:scale-[0.97]";
    const variants = {
      default: "bg-stone-900 text-white hover:bg-stone-800 shadow-sm shadow-stone-900/10",
      outline: "border border-stone-200 bg-white text-stone-700 hover:bg-stone-50 shadow-sm",
      danger:  "bg-red-600 text-white hover:bg-red-500 shadow-sm",
      ghost:   "text-stone-600 hover:bg-stone-100 hover:text-stone-900",
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
