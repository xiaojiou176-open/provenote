import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  label?: string;
}

export function LoadingSpinner({ className, size = "md", label = "Loading" }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
  };

  return (
    <span
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="ui-loading-pulse inline-flex items-center"
    >
      <Loader2
        data-testid="loading-spinner"
        aria-hidden="true"
        className={cn("animate-spin motion-reduce:animate-none", sizeClasses[size], className)}
      />
      <span className="sr-only">{label}</span>
    </span>
  );
}
