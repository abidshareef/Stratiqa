"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { logout } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Sidebar } from "@/components/layout/sidebar";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const hydrated = useAuthStore((s) => s.hydrated);
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const organization = useAuthStore((s) => s.organization);

  useEffect(() => {
    if (hydrated && !accessToken) router.replace("/login");
  }, [hydrated, accessToken, router]);

  if (!hydrated || !accessToken) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  async function handleLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-full flex-1">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-border bg-surface/95 backdrop-blur">
          <div className="flex h-14 items-center justify-between px-5">
            <div className="flex items-center gap-2 text-sm">
              <span className="font-medium">{organization?.name}</span>
              {organization?.industry && (
                <span className="text-muted-foreground">
                  · {organization.industry}
                </span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-xs font-medium leading-none">
                  {user?.full_name ?? user?.email}
                </p>
                <p className="text-[11px] text-muted-foreground">{user?.email}</p>
              </div>
              <div className="flex size-8 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                {(user?.full_name ?? user?.email ?? "?").charAt(0).toUpperCase()}
              </div>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Sign out
              </Button>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
