import React from "react";
import { Pressable, Text, View } from "react-native";
import { StatusBar } from "expo-status-bar";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { AppProviders } from "./src/providers/AppProviders";
import { AppNavigator } from "./src/navigation/AppNavigator";

type ErrorBoundaryState = {
  hasError: boolean;
  message: string;
};

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, message: "" };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, message: error.message || "Unexpected app error" };
  }

  componentDidCatch(error: Error): void {
    console.error("App crash intercepted:", error);
  }

  reset = (): void => {
    this.setState({ hasError: false, message: "" });
  };

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <View style={{ flex: 1, backgroundColor: "#020617", alignItems: "center", justifyContent: "center", padding: 20 }}>
          <Text style={{ color: "#F8FAFC", fontSize: 20, fontWeight: "700", marginBottom: 8 }}>Something went wrong</Text>
          <Text style={{ color: "#FCA5A5", textAlign: "center", marginBottom: 16 }}>{this.state.message}</Text>
          <Pressable
            onPress={this.reset}
            style={{ backgroundColor: "#22D3EE", borderRadius: 10, paddingHorizontal: 16, paddingVertical: 10 }}
          >
            <Text style={{ color: "#020617", fontWeight: "700" }}>Try Again</Text>
          </Pressable>
        </View>
      );
    }

    return this.props.children;
  }
}

export default function App(): React.JSX.Element {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ErrorBoundary>
        <AppProviders>
          <StatusBar style="light" />
          <AppNavigator />
        </AppProviders>
      </ErrorBoundary>
    </GestureHandlerRootView>
  );
}
