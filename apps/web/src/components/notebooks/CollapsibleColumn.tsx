"use client";

import { ChevronLeft, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface CollapsibleColumnProps {
  isCollapsed: boolean;
  onToggle: () => void;
  collapsedIcon: LucideIcon;
  collapsedLabel: string;
  children: ReactNode;
}

export function CollapsibleColumn({
  isCollapsed,
  onToggle,
  collapsedIcon: CollapsedIcon,
  collapsedLabel,
  children,
}: CollapsibleColumnProps) {
  const isCJK = /[\u4e00-\u9fa5\u3040-\u30ff\uac00-\ud7af]/.test(collapsedLabel);

  if (isCollapsed) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onToggle}
              className={cn(
                "h-full min-h-0 w-12 flex-col gap-3 rounded-lg border-border/60 bg-card px-0 py-6",
                "text-muted-foreground shadow-none transition-[background-color,color,transform] duration-150",
                "hover:bg-accent/50 hover:text-foreground",
                "motion-reduce:transition-none motion-reduce:transform-none",
                "group",
              )}
              aria-label={`Expand ${collapsedLabel}`}
            >
              <CollapsedIcon className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors flex-shrink-0" />
              <div
                className={cn(
                  "text-xs font-medium text-muted-foreground group-hover:text-foreground whitespace-nowrap transition-colors",
                  "[writing-mode:vertical-rl] [text-orientation:mixed]",
                  !isCJK && "rotate-180",
                  "motion-reduce:transition-none",
                )}
              >
                {collapsedLabel}
              </div>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">
            <p>Expand {collapsedLabel}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return <div className="h-full min-h-0 transition-all duration-150">{children}</div>;
}

// Factory function to create a collapse button for card headers
export function createCollapseButton(onToggle: () => void, label: string) {
  return (
    <div className="hidden lg:block">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => {
                e.stopPropagation();
                onToggle();
              }}
              className="h-7 w-7 hover:bg-accent"
              aria-label={`Collapse ${label}`}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Collapse {label}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}
