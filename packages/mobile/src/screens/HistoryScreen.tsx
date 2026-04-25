import React, { useMemo } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useQuery } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { listAuditHistory } from "../lib/api";
import type { RootStackParamList } from "../navigation/types";

export function HistoryScreen(): React.JSX.Element {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const historyQuery = useQuery({ queryKey: ["audit-history"], queryFn: listAuditHistory });

  const stats = useMemo(() => {
    const rows = historyQuery.data ?? [];
    const eligible = rows.filter((row) => row.eligible).length;
    const flagged = rows.length - eligible;
    const avgCgpa = rows.length > 0 ? rows.reduce((sum, row) => sum + row.cgpa, 0) / rows.length : 0;
    return {
      total: rows.length,
      eligible,
      flagged,
      avgCgpa,
    };
  }, [historyQuery.data]);

  if (historyQuery.isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#22D3EE" />
      </View>
    );
  }

  if (historyQuery.isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{historyQuery.error.message}</Text>
        <Pressable style={styles.retryButton} onPress={() => historyQuery.refetch()}>
          <Text style={styles.retryLabel}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.content}
      data={historyQuery.data}
      keyExtractor={(item) => item.id}
      refreshControl={
        <RefreshControl
          refreshing={historyQuery.isRefetching}
          onRefresh={() => historyQuery.refetch()}
          tintColor="#22D3EE"
        />
      }
      ListHeaderComponent={
        <View style={styles.hero}>
          <Text style={styles.heroTitle}>Audit Dashboard</Text>
          <Text style={styles.heroSubtitle}>Track every transcript and jump into details fast.</Text>
          <View style={styles.heroStatsRow}>
            <View style={styles.heroStatCard}>
              <Text style={styles.heroStatValue}>{stats.total}</Text>
              <Text style={styles.heroStatLabel}>Total</Text>
            </View>
            <View style={styles.heroStatCard}>
              <Text style={[styles.heroStatValue, { color: "#86EFAC" }]}>{stats.eligible}</Text>
              <Text style={styles.heroStatLabel}>Eligible</Text>
            </View>
            <View style={styles.heroStatCard}>
              <Text style={[styles.heroStatValue, { color: "#FCA5A5" }]}>{stats.flagged}</Text>
              <Text style={styles.heroStatLabel}>Needs Work</Text>
            </View>
            <View style={styles.heroStatCard}>
              <Text style={styles.heroStatValue}>{stats.avgCgpa.toFixed(2)}</Text>
              <Text style={styles.heroStatLabel}>Avg CGPA</Text>
            </View>
          </View>
        </View>
      }
      ListEmptyComponent={<Text style={styles.emptyText}>No audits yet. Open MCP tab to upload and run your first audit.</Text>}
      renderItem={({ item }) => {
        const createdLabel = item.createdAt ? new Date(item.createdAt).toLocaleString() : `Transcript ${item.transcriptId.slice(0, 8)}`;
        return (
          <Pressable
            style={styles.card}
            onPress={() => navigation.navigate("AuditDetail", { transcriptId: item.transcriptId })}
          >
            <View style={styles.rowTop}>
              <View style={styles.programPill}>
                <Ionicons name="school-outline" size={14} color="#67E8F9" />
                <Text style={styles.programLabel}>{item.program}</Text>
              </View>
              <Text style={[styles.statusBadge, item.eligible ? styles.statusOk : styles.statusWarn]}>
                {item.eligible ? "ELIGIBLE" : "NOT ELIGIBLE"}
              </Text>
            </View>

            <View style={styles.metricsRow}>
              <View style={styles.metricBlock}>
                <Text style={styles.metricCaption}>CGPA</Text>
                <Text style={styles.metricValue}>{item.cgpa.toFixed(2)}</Text>
              </View>
              <View style={styles.metricBlock}>
                <Text style={styles.metricCaption}>Credits</Text>
                <Text style={styles.metricValue}>
                  {item.creditsEarned}/{item.totalRequired}
                </Text>
              </View>
              <View style={styles.metricBlock}>
                <Text style={styles.metricCaption}>Issues</Text>
                <Text style={styles.metricValue}>{item.issuesCount}</Text>
              </View>
            </View>

            <View style={styles.cardFooter}>
              <Text style={styles.metaText}>{createdLabel}</Text>
              <Text style={styles.openText}>Open</Text>
            </View>
          </Pressable>
        );
      }}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#020617" },
  content: { padding: 14, gap: 10, paddingBottom: 100 },
  hero: {
    backgroundColor: "#0A1A3A",
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#123768",
    padding: 14,
    gap: 10,
    marginBottom: 6,
  },
  heroTitle: { color: "#F8FAFC", fontSize: 22, fontWeight: "800" },
  heroSubtitle: { color: "#8EA0BC" },
  heroStatsRow: { flexDirection: "row", gap: 8, flexWrap: "wrap" },
  heroStatCard: {
    minWidth: 72,
    backgroundColor: "#081329",
    borderWidth: 1,
    borderColor: "#1C3761",
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  heroStatValue: { color: "#E2E8F0", fontSize: 16, fontWeight: "800" },
  heroStatLabel: { color: "#7E94B8", fontSize: 11, marginTop: 2 },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#020617",
    padding: 16,
  },
  card: {
    backgroundColor: "#091833",
    borderColor: "#16325B",
    borderWidth: 1,
    borderRadius: 16,
    padding: 13,
  },
  rowTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 12 },
  programPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 9,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#1D4B7D",
    backgroundColor: "#0A2144",
  },
  programLabel: { color: "#BAE6FD", fontWeight: "800", fontSize: 13 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999, fontSize: 11, overflow: "hidden", fontWeight: "700" },
  statusOk: { backgroundColor: "#064E3B", color: "#6EE7B7" },
  statusWarn: { backgroundColor: "#7F1D1D", color: "#FCA5A5" },
  metricsRow: { flexDirection: "row", gap: 8, marginBottom: 10 },
  metricBlock: {
    flex: 1,
    backgroundColor: "#081329",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#183760",
    padding: 9,
  },
  metricCaption: { color: "#94A3B8", fontSize: 11 },
  metricValue: { color: "#E2E8F0", fontWeight: "800", marginTop: 2, fontSize: 22 },
  cardFooter: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  metaText: { color: "#7F93B2", fontSize: 12, flex: 1 },
  openText: { color: "#67E8F9", fontWeight: "700", marginLeft: 8 },
  emptyText: { color: "#94A3B8", textAlign: "center", marginTop: 40 },
  errorText: { color: "#FCA5A5", textAlign: "center", marginBottom: 10 },
  retryButton: { backgroundColor: "#22D3EE", borderRadius: 10, paddingHorizontal: 14, paddingVertical: 10 },
  retryLabel: { color: "#020617", fontWeight: "700" },
});
