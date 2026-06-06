"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FileText,
  FolderKanban,
  LayoutDashboard,
  Lightbulb,
  Network,
  Siren,
  Sparkles,
  Target,
} from "lucide-react";

import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "STRATIQA One", icon: LayoutDashboard },
  { href: "/war-room", label: "War Room", icon: Siren },
  { href: "/goals", label: "Goals", icon: Target },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/recommendations", label: "Recommendations", icon: Lightbulb },
  { href: "/twin", label: "Business Twin", icon: Network },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/ask", label: "Ask", icon: Sparkles },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-56 shrink-0 border-r border-border bg-surface md:flex md:flex-col">
      <div className="flex h-14 items-center gap-2 border-b border-border px-5">
        <div className="h-2 w-2 rounded-full bg-primary" />
        <span className="text-sm font-semibold tracking-tight">STRATIQA</span>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-card text-foreground"
                  : "text-muted hover:bg-card hover:text-foreground",
              )}
            >
              <Icon className="size-4" />
              {label}
              {active && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-4">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
          Intelligence before analytics
        </p>
      </div>
    </aside>
  );
}
