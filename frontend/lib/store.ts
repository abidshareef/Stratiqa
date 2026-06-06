"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { OrganizationOut, UserOut } from "./types";

interface AuthState {
  user: UserOut | null;
  organization: OrganizationOut | null;
  accessToken: string | null;
  refreshToken: string | null;
  /** True once zustand has rehydrated from localStorage (avoids guard flicker). */
  hydrated: boolean;
  setSession: (s: {
    user: UserOut;
    organization: OrganizationOut;
    accessToken: string;
    refreshToken: string;
  }) => void;
  clear: () => void;
  setHydrated: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      organization: null,
      accessToken: null,
      refreshToken: null,
      hydrated: false,
      setSession: ({ user, organization, accessToken, refreshToken }) =>
        set({ user, organization, accessToken, refreshToken }),
      clear: () =>
        set({
          user: null,
          organization: null,
          accessToken: null,
          refreshToken: null,
        }),
      setHydrated: () => set({ hydrated: true }),
    }),
    {
      name: "stratiqa-auth",
      onRehydrateStorage: () => (state) => state?.setHydrated(),
      partialize: (s) => ({
        user: s.user,
        organization: s.organization,
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
      }),
    },
  ),
);
