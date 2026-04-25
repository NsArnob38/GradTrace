import React from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";
import { useAuth } from "../contexts/AuthContext";

export function SettingsScreen(): React.JSX.Element {
  const { session, signOut } = useAuth();

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      Alert.alert("Sign out failed", error instanceof Error ? error.message : "Unexpected error");
    }
  };

  return (
    <View style={styles.screen}>
      <View style={styles.card}>
        <Text style={styles.heading}>Account</Text>
        <Text style={styles.value}>{session?.user.email ?? "Unknown email"}</Text>
      </View>

      <Pressable style={styles.button} onPress={handleSignOut}>
        <Text style={styles.buttonLabel}>Sign Out</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#020617",
    padding: 16,
    gap: 12,
  },
  card: {
    borderColor: "#1E293B",
    borderWidth: 1,
    borderRadius: 14,
    backgroundColor: "#0F172A",
    padding: 12,
  },
  heading: { color: "#94A3B8", fontSize: 12, textTransform: "uppercase", marginBottom: 8 },
  value: { color: "#E2E8F0", fontSize: 16, fontWeight: "600" },
  button: {
    backgroundColor: "#7F1D1D",
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
  },
  buttonLabel: { color: "#FEE2E2", fontWeight: "700" },
});
