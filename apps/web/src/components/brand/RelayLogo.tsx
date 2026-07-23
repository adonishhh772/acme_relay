import { Link } from "react-router-dom";

import { ORGANISATION_NAME, PRODUCT_NAME, SHELL_NAME } from "../../constants/branding";
import { cn } from "../../lib/cn";

type LogoSize = "sm" | "md" | "lg";
type LogoVariant = "light" | "dark";

type RelayLogoProps = {
  size?: LogoSize;
  variant?: LogoVariant;
  showTagline?: boolean;
  className?: string;
  to?: string;
};

const sizes: Record<LogoSize, { icon: string; title: string; tag: string }> = {
  sm: { icon: "h-8 w-8", title: "text-sm", tag: "text-[10px]" },
  md: { icon: "h-9 w-9", title: "text-base", tag: "text-xs" },
  lg: { icon: "h-12 w-12", title: "text-2xl", tag: "text-sm" },
};

export function RelayLogo({
  size = "md",
  variant = "dark",
  showTagline = true,
  className,
  to,
}: RelayLogoProps) {
  const sizeStyles = sizes[size];
  const titleClass = variant === "light" ? "text-white" : "text-ink-primary";
  const tagClass = variant === "light" ? "text-slate-400" : "text-ink-muted";
  const rootClass = cn("flex items-center gap-3", className);

  const content = (
    <>
      <div
        className={cn(
          sizeStyles.icon,
          "flex shrink-0 items-center justify-center rounded-2xl bg-relay-cyan text-white shadow-soft",
        )}
        aria-hidden
      >
        <svg viewBox="0 0 24 24" className="h-[55%] w-[55%]" fill="none">
          <path d="M4 12 H14" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
          <path
            d="M12 7 L18 12 L12 17"
            stroke="white"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <div className="min-w-0">
        <p className={cn(sizeStyles.title, "font-display font-semibold tracking-tight", titleClass)}>
          {PRODUCT_NAME}
          <span className="font-medium text-relay-mint"> · {SHELL_NAME}</span>
        </p>
        {showTagline ? (
          <p className={cn(sizeStyles.tag, "font-medium tracking-wide", tagClass)}>
            {ORGANISATION_NAME}
          </p>
        ) : null}
      </div>
    </>
  );

  if (to) {
    return (
      <Link to={to} className={rootClass} aria-label="Go to assistant">
        {content}
      </Link>
    );
  }

  return <div className={rootClass}>{content}</div>;
}
