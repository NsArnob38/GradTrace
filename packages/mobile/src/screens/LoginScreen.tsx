import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useAuth } from "../contexts/AuthContext";
import { registerAccount } from "../lib/api";

export function LoginScreen(): React.JSX.Element {
  const { signIn, signInWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const handleLogin = async () => {
    setError("");
    setInfo("");
    if (!email || !password) {
      setError("Email and password are required");
      return;
    }
    setLoading(true);
    try {
      await signIn(email.trim(), password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      setLoading(false);
      return;
    }
    setLoading(false);
  };

  const handleCreateAccount = async () => {
    setError("");
    setInfo("");
    if (!email || !password) {
      setError("Email and password are required");
      return;
    }
    setLoading(true);
    try {
      const result = await registerAccount(email.trim(), password);
      setInfo(result.message || "Account ready. Signing you in...");
      await signIn(email.trim(), password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account");
      setLoading(false);
      return;
    }
    setLoading(false);
  };

  const handleGoogleLogin = async () => {
    setError("");
    setInfo("");
    setLoading(true);
    try {
      await signInWithGoogle();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google login failed");
      setLoading(false);
      return;
    }
    setLoading(false);
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.select({ ios: "padding", android: undefined })}
      style={styles.screen}
    >
      <View style={styles.card}>
        <Text style={styles.title}>GradeTrace</Text>
        <Text style={styles.subtitle}>Sign in with your NSU account</Text>

        <Pressable style={styles.googleButton} disabled={loading} onPress={handleGoogleLogin}>
          {loading ? <ActivityIndicator color="#020617" /> : <Text style={styles.googleButtonLabel}>Continue with NSU Google</Text>}
        </Pressable>
        <Text style={styles.orLabel}>or use email and password</Text>

        <TextInput
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
          placeholder="NSU Email"
          placeholderTextColor="#64748B"
          style={styles.input}
        />
        <TextInput
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          placeholder="Password"
          placeholderTextColor="#64748B"
          style={styles.input}
        />

        {!!error && <Text style={styles.error}>{error}</Text>}
        {!!info && <Text style={styles.info}>{info}</Text>}

        <Pressable style={styles.button} disabled={loading} onPress={handleLogin}>
          {loading ? <ActivityIndicator color="#020617" /> : <Text style={styles.buttonLabel}>Sign In</Text>}
        </Pressable>

        <Pressable style={styles.secondaryButton} disabled={loading} onPress={handleCreateAccount}>
          <Text style={styles.secondaryButtonLabel}>Create Account / Set Password</Text>
        </Pressable>

      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#020617",
    alignItems: "center",
    justifyContent: "center",
    padding: 20,
  },
  card: {
    width: "100%",
    maxWidth: 420,
    backgroundColor: "#0F172A",
    borderRadius: 16,
    borderColor: "#1E293B",
    borderWidth: 1,
    padding: 18,
    gap: 10,
  },
  title: {
    color: "#F8FAFC",
    fontSize: 26,
    fontWeight: "700",
  },
  subtitle: {
    color: "#94A3B8",
    marginBottom: 4,
  },
  googleButton: {
    backgroundColor: "#E2E8F0",
    borderRadius: 10,
    alignItems: "center",
    paddingVertical: 12,
    marginTop: 4,
    marginBottom: 2,
  },
  googleButtonLabel: {
    color: "#020617",
    fontWeight: "700",
  },
  orLabel: {
    color: "#64748B",
    textAlign: "center",
    marginBottom: 4,
  },
  input: {
    backgroundColor: "#0B1220",
    borderColor: "#334155",
    borderWidth: 1,
    borderRadius: 10,
    color: "#E2E8F0",
    paddingHorizontal: 12,
    paddingVertical: 11,
  },
  button: {
    backgroundColor: "#22D3EE",
    borderRadius: 10,
    alignItems: "center",
    paddingVertical: 12,
    marginTop: 8,
  },
  buttonLabel: {
    color: "#020617",
    fontWeight: "700",
  },
  error: {
    color: "#FCA5A5",
    marginTop: 4,
  },
  info: {
    color: "#7DD3FC",
    marginTop: 4,
  },
  secondaryButton: {
    borderRadius: 10,
    alignItems: "center",
    paddingVertical: 12,
    marginTop: 2,
    borderWidth: 1,
    borderColor: "#334155",
  },
  secondaryButtonLabel: {
    color: "#CBD5E1",
    fontWeight: "600",
  },
});
