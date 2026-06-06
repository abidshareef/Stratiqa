import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      tone: {
        neutral: "border-border bg-surface text-muted",
        info: "border-info/30 bg-info/10 text-info",
        success: "border-success/30 bg-success/10 text-success",
        warning: "border-warning/30 bg-warning/10 text-warning",
        danger: "border-danger/30 bg-danger/10 text-danger",
      },
    },
    defaultVariants: {
      tone: "neutral",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}

/** Map a backend severity/risk string to a badge tone. */
export function toneForLevel(level: string): NonNullable<BadgeProps["tone"]> {
  switch (level.toLowerCase()) {
    case "critical":
    case "high":
    case "danger":
      return "danger";
    case "medium":
    case "warning":
      return "warning";
    case "low":
    case "success":
    case "on_track":
      return "success";
    case "info":
      return "info";
    default:
      return "neutral";
  }
}

export { Badge, badgeVariants };
