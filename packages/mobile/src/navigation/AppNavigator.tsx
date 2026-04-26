import React from "react";
import { ActivityIndicator, View, Text } from "react-native";
import { NavigationContainer, DarkTheme } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Ionicons, MaterialCommunityIcons } from "@expo/vector-icons";
import { useAuth } from "../contexts/AuthContext";
import { LoginScreen } from "../screens/LoginScreen";
import { HistoryScreen } from "../screens/HistoryScreen";
import { UploadScreen } from "../screens/UploadScreen";
import { SettingsScreen } from "../screens/SettingsScreen";
import { AuditDetailScreen } from "../screens/AuditDetailScreen";
import { AdminScreen } from "../screens/AdminScreen";
import type { MainTabParamList, RootStackParamList } from "./types";

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

function MainTabsNavigator(): React.JSX.Element {
  return (
    <Tab.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: "#0F172A" },
        headerTintColor: "#F8FAFC",
        tabBarStyle: {
          backgroundColor: "#071129",
          borderTopColor: "#112244",
          borderTopWidth: 1,
          height: 72,
          paddingTop: 6,
          paddingBottom: 8,
        },
        tabBarActiveTintColor: "#23E0FF",
        tabBarInactiveTintColor: "#8EA0BC",
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "700",
          letterSpacing: 0.2,
        },
      }}
    >
      <Tab.Screen
        name="History"
        component={HistoryScreen}
        options={{
          title: "Audits",
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons name={focused ? "reader" : "reader-outline"} size={size + 1} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Upload"
        component={UploadScreen}
        options={{
          title: "Audit",
          headerTitle: "Audit Studio",
          tabBarIcon: ({ focused }) => (
            <View
              style={{
                width: 44,
                height: 44,
                borderRadius: 22,
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: focused ? "#22D3EE" : "#0C2B3A",
                borderWidth: 1,
                borderColor: focused ? "#67E8F9" : "#155E75",
                marginTop: -2,
              }}
            >
              <MaterialCommunityIcons
                name={focused ? "file-document-edit" : "file-document-edit-outline"}
                size={22}
                color={focused ? "#041019" : "#67E8F9"}
              />
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: "Settings",
          tabBarIcon: ({ color, focused, size }) => (
            <Ionicons name={focused ? "settings" : "settings-outline"} size={size + 1} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

function LoadingScreen(): React.JSX.Element {
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#020617" }}>
      <ActivityIndicator size="large" color="#22D3EE" />
      <Text style={{ color: "#CBD5E1", marginTop: 10 }}>Loading session...</Text>
    </View>
  );
}

export function AppNavigator(): React.JSX.Element {
  const { session, isAdmin, loading } = useAuth();

  if (loading) return <LoadingScreen />;

  return (
    <NavigationContainer theme={DarkTheme}>
      {session ? (
        <Stack.Navigator>
          <Stack.Screen
            name="MainTabs"
            component={MainTabsNavigator}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="AuditDetail"
            component={AuditDetailScreen}
            options={{
              title: "Audit Detail",
              headerStyle: { backgroundColor: "#0F172A" },
              headerTintColor: "#F8FAFC",
            }}
          />
        </Stack.Navigator>
      ) : isAdmin ? (
        <Stack.Navigator>
          <Stack.Screen
            name="AdminHome"
            component={AdminScreen}
            options={{
              title: "Admin",
              headerStyle: { backgroundColor: "#0F172A" },
              headerTintColor: "#F8FAFC",
            }}
          />
        </Stack.Navigator>
      ) : (
        <LoginScreen />
      )}
    </NavigationContainer>
  );
}
