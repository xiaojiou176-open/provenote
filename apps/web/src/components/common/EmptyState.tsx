import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div
      className="ui-empty-state ui-empty-state-surface mx-auto max-w-2xl rounded-[1.5rem] px-6 py-12 text-center"
      role="status"
      aria-live="polite"
    >
      <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-border/70 bg-card/90 shadow-[0_12px_24px_oklch(18%_0.02_45deg_/6%)]">
        <Icon className="ui-empty-icon h-8 w-8 text-primary/70" />
      </div>
      <h3 className="mb-2 font-serif text-[1.65rem] leading-none tracking-[-0.03em] text-foreground">
        {title}
      </h3>
      <p className="mx-auto mb-4 max-w-xl text-sm leading-6 text-muted-foreground">{description}</p>
      {action}
    </div>
  );
}
