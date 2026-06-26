"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, registerAuthFailureCallback, unregisterAuthFailureCallback } from './api';
import { LoginPayload, RegisterPayload, TokenResponse, User } from './types';

const ACCESS_TOKEN_KEY = 'meetingai_access_token';
const REFRESH_TOKEN_KEY = 'meetingai_refresh_token';
const USER_KEY = 'meetingai_user';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginPayload) => Promise<void>;
  register: (data: RegisterPayload) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isReady: boolean;
}

const defaultAuthContext: AuthContextType = {
  user: null,
  token: null,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  isAuthenticated: false,
  isReady: true,
};

const AuthContext = createContext<AuthContextType>(defaultAuthContext);

function persistAuth(response: TokenResponse) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(response.user));
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const router = useRouter();

  // ── Logout (stable ref via useCallback) ─────────────────────────────
  const logout = useCallback(() => {
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
    router.push('/login');
  }, [router]);

  // ── Hydrate from localStorage on mount ──────────────────────────────
  useEffect(() => {
    const storedToken = window.localStorage.getItem(ACCESS_TOKEN_KEY);
    const storedUser = window.localStorage.getItem(USER_KEY);
    setToken(storedToken);
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        window.localStorage.removeItem(USER_KEY);
      }
    }
    setIsReady(true);
  }, []);

  // ── Register auth failure callback so the API layer can trigger
  //    automatic logout when refresh token is expired/invalid ──────────
  useEffect(() => {
    registerAuthFailureCallback(logout);
    return () => unregisterAuthFailureCallback();
  }, [logout]);

  // ── Keep React state in sync when the API layer does a silent
  //    token refresh (it writes directly to localStorage) ─────────────
  useEffect(() => {
    function handleStorageChange(e: StorageEvent) {
      if (e.key === ACCESS_TOKEN_KEY) {
        setToken(e.newValue);
      }
      if (e.key === USER_KEY && e.newValue) {
        try {
          setUser(JSON.parse(e.newValue));
        } catch {
          /* ignore malformed data */
        }
      }
      // If tokens were cleared from another tab, sync logout
      if (e.key === ACCESS_TOKEN_KEY && e.newValue === null) {
        setUser(null);
        setToken(null);
        router.push('/login');
      }
    }

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [router]);

  const login = async (credentials: LoginPayload) => {
    const response = await api.login(credentials);
    persistAuth(response);
    setToken(response.access_token);
    setUser(response.user);
    router.push('/dashboard');
  };

  const register = async (data: RegisterPayload) => {
    const response = await api.register(data);
    persistAuth(response);
    setToken(response.access_token);
    setUser(response.user);
    router.push('/dashboard');
  };

  const value = useMemo(
    () => ({
      user,
      token,
      login,
      register,
      logout,
      isAuthenticated: Boolean(token && user),
      isReady,
    }),
    [user, token, isReady, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

