"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { removeToken, fetchWithAuth } from "@/lib/auth";

export interface User {
  id: string;
  login: string;
  name: string | null;
  email: string | null;
  avatar_url: string | null;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      try {
        const res = await fetchWithAuth(`${apiBase}/api/v1/auth/me`);
        if (res.ok) {
          const userData = await res.json();
          setUser(userData);
        } else {
          removeToken();
        }
      } catch (e) {
        console.error("Failed to fetch user", e);
      } finally {
        setIsLoading(false);
      }
    }
    loadUser();
  }, []);

  const logout = () => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    fetchWithAuth(`${apiBase}/api/v1/auth/logout`, { method: "POST" })
      .catch(() => {})
      .finally(() => {
        removeToken();
        setUser(null);
        window.location.href = "/";
      });
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
