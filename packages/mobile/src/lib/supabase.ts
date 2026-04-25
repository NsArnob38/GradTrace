import * as SecureStore from "expo-secure-store";
import { createClient } from "@supabase/supabase-js";
import { env } from "./env";

const secureStorage = {
  getItem: (key: string): Promise<string | null> => SecureStore.getItemAsync(key),
  setItem: (key: string, value: string): Promise<void> =>
    SecureStore.setItemAsync(key, value).then(() => undefined),
  removeItem: (key: string): Promise<void> =>
    SecureStore.deleteItemAsync(key).then(() => undefined),
};

export const supabase = createClient(env.supabaseUrl, env.supabaseAnonKey, {
  auth: {
    storage: secureStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});
