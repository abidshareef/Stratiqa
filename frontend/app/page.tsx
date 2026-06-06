"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuthStore } from "@/lib/store";

export default function Home() {
  const router = useRouter();
  const hydrated = useAuthStore((s) => s.hydrated);
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    if (!hydrated) return;
    router.replace(accessToken ? "/dashboard" : "/login");
  }, [hydrated, accessToken, router]);

  return (
    <main className="flex flex-1 items-center justify-center">
      <p className="text-sm text-muted-foreground">Loading STRATIQA…</p>
    </main>
  );
}
