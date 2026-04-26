import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import * as AuthSession from "expo-auth-session";
import * as WebBrowser from "expo-web-browser";
import * as SecureStore from "expo-secure-store";
import { supabase } from "../lib/supabase";
import { adminLogin } from "../lib/api";

WebBrowser.maybeCompleteAuthSession();

const NSU_DOMAIN = "northsouth.edu";

type AuthContextValue = {
  session: Session | null;
  adminToken: string | null;
  adminId: string | null;
  isAdmin: boolean;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signInAdmin: (adminId: string, password: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  signOutAdmin: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

type Props = {
  children: React.ReactNode;
};

const ADMIN_TOKEN_KEY = "gradetrace_admin_token";
const ADMIN_ID_KEY = "gradetrace_admin_id";

export function AuthProvider({ children }: Props): React.JSX.Element {
  const [session, setSession] = useState<Session | null>(null);
  const [adminToken, setAdminToken] = useState<string | null>(null);
  const [adminId, setAdminId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.all([
      supabase.auth.getSession(),
      SecureStore.getItemAsync(ADMIN_TOKEN_KEY),
      SecureStore.getItemAsync(ADMIN_ID_KEY),
    ])
      .then(([sessionResult, savedAdminToken, savedAdminId]) => {
        if (!active) return;
        setSession(sessionResult.data.session);
        setAdminToken(savedAdminToken);
        setAdminId(savedAdminId);
        setLoading(false);
      })
      .catch(() => {
        if (active) setLoading(false);
      });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setLoading(false);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      adminToken,
      adminId,
      isAdmin: Boolean(adminToken),
      loading,
      signIn: async (email: string, password: string) => {
        await SecureStore.deleteItemAsync(ADMIN_TOKEN_KEY);
        await SecureStore.deleteItemAsync(ADMIN_ID_KEY);
        setAdminToken(null);
        setAdminId(null);
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      },
      signInAdmin: async (nextAdminId: string, password: string) => {
        await supabase.auth.signOut();
        const result = await adminLogin(nextAdminId, password);
        await SecureStore.setItemAsync(ADMIN_TOKEN_KEY, result.token);
        await SecureStore.setItemAsync(ADMIN_ID_KEY, result.admin_id);
        setSession(null);
        setAdminToken(result.token);
        setAdminId(result.admin_id);
      },
      signInWithGoogle: async () => {
        await SecureStore.deleteItemAsync(ADMIN_TOKEN_KEY);
        await SecureStore.deleteItemAsync(ADMIN_ID_KEY);
        setAdminToken(null);
        setAdminId(null);
        const redirectTo = AuthSession.makeRedirectUri({
          scheme: "gradetrace",
          path: "oauth/callback",
        });

        const { data, error } = await supabase.auth.signInWithOAuth({
          provider: "google",
          options: {
            redirectTo,
            skipBrowserRedirect: true,
            queryParams: {
              prompt: "select_account",
              hd: NSU_DOMAIN,
            },
          },
        });

        if (error) throw error;
        if (!data?.url) throw new Error("Unable to start Google sign-in.");

        const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
        if (result.type !== "success" || !result.url) {
          throw new Error("Google sign-in was cancelled or redirect URL is not configured for this app.");
        }

        const callbackUrl = new URL(result.url);
        const code = callbackUrl.searchParams.get("code");
        if (code) {
          const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
          if (exchangeError) throw exchangeError;
        } else {
          const hash = callbackUrl.hash.startsWith("#") ? callbackUrl.hash.slice(1) : callbackUrl.hash;
          const params = new URLSearchParams(hash);
          const accessToken = params.get("access_token");
          const refreshToken = params.get("refresh_token");
          if (!accessToken || !refreshToken) {
            throw new Error("Google sign-in redirect did not contain a usable session.");
          }
          const { error: sessionError } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          });
          if (sessionError) throw sessionError;
        }

        const {
          data: { session },
        } = await supabase.auth.getSession();
        const email = session?.user?.email?.toLowerCase() ?? "";
        if (!email.endsWith(`@${NSU_DOMAIN}`)) {
          await supabase.auth.signOut();
          throw new Error(`Please use your @${NSU_DOMAIN} Google account.`);
        }
      },
      signOut: async () => {
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
      },
      signOutAdmin: async () => {
        await SecureStore.deleteItemAsync(ADMIN_TOKEN_KEY);
        await SecureStore.deleteItemAsync(ADMIN_ID_KEY);
        setAdminToken(null);
        setAdminId(null);
      },
    }),
    [adminId, adminToken, loading, session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
