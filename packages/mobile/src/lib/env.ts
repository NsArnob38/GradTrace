import { z } from "zod";

const EnvSchema = z.object({
  EXPO_PUBLIC_SUPABASE_URL: z.string().url(),
  EXPO_PUBLIC_SUPABASE_ANON_KEY: z.string().min(10),
  EXPO_PUBLIC_API_URL: z.string().url(),
  EXPO_PUBLIC_MCP_URL: z.string().url(),
  EXPO_PUBLIC_WEB_URL: z.string().url().optional(),
});

const parsed = EnvSchema.safeParse({
  EXPO_PUBLIC_SUPABASE_URL: process.env.EXPO_PUBLIC_SUPABASE_URL,
  EXPO_PUBLIC_SUPABASE_ANON_KEY: process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY,
  EXPO_PUBLIC_API_URL: process.env.EXPO_PUBLIC_API_URL,
  EXPO_PUBLIC_MCP_URL: process.env.EXPO_PUBLIC_MCP_URL,
  EXPO_PUBLIC_WEB_URL: process.env.EXPO_PUBLIC_WEB_URL,
});

if (!parsed.success) {
  throw new Error(
    "Invalid mobile env configuration. Check EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY, EXPO_PUBLIC_API_URL, EXPO_PUBLIC_MCP_URL."
  );
}

export const env = {
  supabaseUrl: parsed.data.EXPO_PUBLIC_SUPABASE_URL,
  supabaseAnonKey: parsed.data.EXPO_PUBLIC_SUPABASE_ANON_KEY,
  apiUrl: parsed.data.EXPO_PUBLIC_API_URL.replace(/\/+$/, ""),
  mcpUrl: parsed.data.EXPO_PUBLIC_MCP_URL.replace(/\/+$/, ""),
  webUrl: parsed.data.EXPO_PUBLIC_WEB_URL?.replace(/\/+$/, "") ?? null,
};
