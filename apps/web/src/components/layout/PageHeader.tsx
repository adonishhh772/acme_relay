import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type PageHeaderProps = {
  icon: LucideIcon;
  title: string;
  description: string;
  actions?: ReactNode;
  testId?: string;
  className?: string;
};

export function PageHeader({
  icon: Icon,
  title,
  description,
  actions,
  testId,
  className = "mb-6",
}: PageHeaderProps) {
  return (
    <header
      className={`flex flex-wrap items-start justify-between gap-4 ${className}`}
      data-testid={testId}
    >
      <div className="flex items-start gap-2">
        <Icon className="mt-1 h-5 w-5 shrink-0 text-relay-cyan" aria-hidden />
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink-primary">
            {title}
          </h1>
          <p className="page-lead mt-1 max-w-3xl">{description}</p>
        </div>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}
