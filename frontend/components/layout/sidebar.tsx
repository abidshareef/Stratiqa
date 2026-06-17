"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  ChevronDown,
  FileText,
  FolderKanban,
  LayoutDashboard,
  Lightbulb,
  Network,
  Package,
  Share2,
  ShieldCheck,
  Siren,
  Sparkles,
  Target,
  TriangleAlert,
  Upload,
  Users,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

// The everyday cockpit — kept short so the rail reads easy at a glance.
const PRIMARY: NavItem[] = [
  { href: "/dashboard", label: "STRATIQA One", icon: LayoutDashboard },
  { href: "/war-room", label: "War Room", icon: Siren },
  { href: "/ask", label: "Ask", icon: Sparkles },
  { href: "/goals", label: "Goals", icon: Target },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/customers", label: "Customers", icon: Users },
  { href: "/products", label: "Products", icon: Package },
  { href: "/recommendations", label: "Recommendations", icon: Lightbulb },
];

// Deeper models, monitoring, ingestion, reporting, admin — tucked under "More".
const MORE: NavItem[] = [
  { href: "/alerts", label: "Alerts", icon: TriangleAlert },
  { href: "/agents", label: "AI Agents", icon: Bot },
  { href: "/twin", label: "Business Twin", icon: Network },
  { href: "/graph", label: "Knowledge Graph", icon: Share2 },
  { href: "/data", label: "Data Ingestion", icon: Upload },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/governance", label: "Governance", icon: ShieldCheck },
];

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar() {
  const pathname = usePathname();
  const inMore = MORE.some((i) => isActive(pathname, i.href));
  // Open "More" by default only when the user is already on one of its pages.
  const [moreOpen, setMoreOpen] = useState(inMore);

  return (
    <aside className="hidden w-60 shrink-0 border-r border-border bg-surface md:flex md:flex-col">
      <div className="flex h-14 items-center gap-2.5 border-b border-border px-5">
        <div className="flex size-7 items-center justify-center rounded-md bg-primary/15 ring-1 ring-inset ring-primary/30">
          <span className="metric text-sm font-bold text-primary">S</span>
        </div>
        <div className="leading-none">
          <span className="text-sm font-semibold tracking-tight">STRATIQA</span>
          <p className="mt-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">
            Business OS
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {PRIMARY.map((item) => (
          <NavLink key={item.href} item={item} pathname={pathname} />
        ))}

        {/* Divider before the secondary group */}
        <div className="!my-2 border-t border-border/60" />

        <button
          type="button"
          onClick={() => setMoreOpen((o) => !o)}
          aria-expanded={moreOpen}
          className={cn(
            "flex w-full items-center gap-3 rounded-md py-2 pl-3 pr-2 text-sm transition-colors",
            !moreOpen && inMore
              ? "text-foreground"
              : "text-muted hover:bg-card/60 hover:text-foreground",
          )}
        >
          <ChevronDown
            className={cn(
              "size-4 shrink-0 text-muted-foreground transition-transform",
              moreOpen ? "rotate-0" : "-rotate-90",
            )}
          />
          More
          {!moreOpen && inMore && (
            <span className="ml-auto size-1.5 rounded-full bg-primary" />
          )}
        </button>

        {moreOpen && (
          <div className="space-y-1">
            {MORE.map((item) => (
              <NavLink key={item.href} item={item} pathname={pathname} />
            ))}
          </div>
        )}
      </nav>

      <div className="border-t border-border p-4">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
          Intelligence before analytics
        </p>
      </div>
    </aside>
  );
}

function NavLink({
  item,
  pathname,
}: {
  item: NavItem;
  pathname: string;
}) {
  const { href, label, icon: Icon } = item;
  const active = isActive(pathname, href);
  return (
    <Link
      href={href}
      className={cn(
        "group relative flex items-center gap-3 rounded-md py-2 pl-3 pr-2 text-sm transition-colors",
        active
          ? "bg-card font-medium text-foreground"
          : "text-muted hover:bg-card/60 hover:text-foreground",
      )}
    >
      {/* Left accent bar marks the active route. */}
      <span
        className={cn(
          "absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r-full bg-primary transition-opacity",
          active ? "opacity-100" : "opacity-0",
        )}
      />
      <Icon
        className={cn(
          "size-4 shrink-0 transition-colors",
          active ? "text-primary" : "text-muted-foreground",
        )}
      />
      {label}
    </Link>
  );
}
