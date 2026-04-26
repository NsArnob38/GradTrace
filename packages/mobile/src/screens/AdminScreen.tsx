import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useAuth } from "../contexts/AuthContext";
import {
  addAdminAccount,
  deleteProgram,
  getAdminStats,
  listAdminAccounts,
  listAdminAudits,
  listAdminStudents,
  listProgramCourses,
  removeAdminAccount,
  saveProgramCourses,
  type MobileAdminAudit,
  type MobileAdminStats,
  type MobileAdminStudent,
  type MobileProgramCourse,
} from "../lib/api";

type Tab = "overview" | "students" | "audits" | "programs" | "admins";

type EditableProgramCourse = {
  course_code: string;
  course_name: string;
  credits: string;
  category: string;
};

const NEW_PROGRAM = "__NEW_PROGRAM__";

export function AdminScreen(): React.JSX.Element {
  const { adminToken, adminId, signOutAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState<MobileAdminStats | null>(null);
  const [students, setStudents] = useState<MobileAdminStudent[]>([]);
  const [audits, setAudits] = useState<MobileAdminAudit[]>([]);
  const [admins, setAdmins] = useState<string[]>([]);
  const [programs, setPrograms] = useState<MobileProgramCourse[]>([]);
  const [query, setQuery] = useState("");
  const [newAdminId, setNewAdminId] = useState("");
  const [newAdminPassword, setNewAdminPassword] = useState("");
  const [selectedProgramCode, setSelectedProgramCode] = useState(NEW_PROGRAM);
  const [programCodeInput, setProgramCodeInput] = useState("");
  const [programRows, setProgramRows] = useState<EditableProgramCourse[]>([]);
  const [programMessage, setProgramMessage] = useState("");
  const selectedProgramCodeRef = useRef(selectedProgramCode);

  useEffect(() => {
    selectedProgramCodeRef.current = selectedProgramCode;
  }, [selectedProgramCode]);

  const programCodes = useMemo(
    () => Array.from(new Set(programs.map((row) => row.program_code))).sort(),
    [programs]
  );

  const filteredStudents = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return students;
    return students.filter((student) =>
      [student.email, student.full_name, student.student_id, student.program]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle))
    );
  }, [query, students]);

  const loadProgramEditor = (allRows: MobileProgramCourse[], programCode: string) => {
    const rows = allRows
      .filter((row) => row.program_code === programCode)
      .sort((a, b) => a.course_code.localeCompare(b.course_code))
      .map((row) => ({
        course_code: row.course_code,
        course_name: row.course_name,
        credits: String(row.credits),
        category: row.category,
      }));
    setSelectedProgramCode(programCode);
    setProgramCodeInput(programCode);
    setProgramRows(rows);
    setProgramMessage("");
  };

  const startNewProgram = () => {
    setSelectedProgramCode(NEW_PROGRAM);
    setProgramCodeInput("");
    setProgramRows([]);
    setProgramMessage("");
  };

  const reloadPrograms = async (token: string, preferredProgram?: string) => {
    const rows = await listProgramCourses(token);
    const normalized = rows.map((row) => ({
      ...row,
      program_code: row.program_code.toUpperCase(),
      course_code: row.course_code.toUpperCase(),
    }));
    setPrograms(normalized);
    const nextProgram = preferredProgram && normalized.some((row) => row.program_code === preferredProgram)
      ? preferredProgram
      : normalized[0]?.program_code;
    if (nextProgram) {
      loadProgramEditor(normalized, nextProgram);
    } else {
      startNewProgram();
    }
  };

  useEffect(() => {
    if (!adminToken) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        if (activeTab === "overview") {
          const data = await getAdminStats(adminToken);
          if (!cancelled) setStats(data);
        } else if (activeTab === "students") {
          const data = await listAdminStudents(adminToken);
          if (!cancelled) setStudents(data);
        } else if (activeTab === "audits") {
          const data = await listAdminAudits(adminToken);
          if (!cancelled) setAudits(data);
        } else if (activeTab === "admins") {
          const data = await listAdminAccounts(adminToken);
          if (!cancelled) setAdmins(data);
        } else {
          const currentProgramCode = selectedProgramCodeRef.current;
          await reloadPrograms(adminToken, currentProgramCode !== NEW_PROGRAM ? currentProgramCode : undefined);
        }
      } catch (nextError) {
        if (!cancelled) setError(nextError instanceof Error ? nextError.message : "Failed to load admin data");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [activeTab, adminToken]);

  if (!adminToken) {
    return (
      <View style={styles.screenCenter}>
        <Text style={styles.emptyText}>Admin session not found.</Text>
      </View>
    );
  }

  const saveProgram = async () => {
    const normalizedProgramCode = programCodeInput.trim().toUpperCase();
    if (!normalizedProgramCode) {
      setProgramMessage("Program code is required.");
      return;
    }
    if (programRows.length === 0) {
      setProgramMessage("Add at least one course before saving.");
      return;
    }

    const payload: MobileProgramCourse[] = [];
    for (const row of programRows) {
      const courseCode = row.course_code.trim().toUpperCase().replace(/\s+/g, "");
      const credits = Number(row.credits);
      if (!courseCode || !row.course_name.trim() || !row.category.trim() || !Number.isFinite(credits)) {
        setProgramMessage("Each course needs code, name, credits, and category.");
        return;
      }
      payload.push({
        program_code: normalizedProgramCode,
        course_code: courseCode,
        course_name: row.course_name.trim(),
        credits,
        category: row.category.trim(),
      });
    }

    try {
      await saveProgramCourses(adminToken, payload);
      await reloadPrograms(adminToken, normalizedProgramCode);
      setProgramMessage(`Saved ${payload.length} courses for ${normalizedProgramCode}.`);
    } catch (nextError) {
      setProgramMessage(nextError instanceof Error ? nextError.message : "Failed to save program.");
    }
  };

  const removeProgram = async () => {
    const normalizedProgramCode = programCodeInput.trim().toUpperCase();
    if (!normalizedProgramCode) return;
    try {
      await deleteProgram(adminToken, normalizedProgramCode);
      await reloadPrograms(adminToken);
      setProgramMessage(`Deleted ${normalizedProgramCode}.`);
    } catch (nextError) {
      setProgramMessage(nextError instanceof Error ? nextError.message : "Failed to delete program.");
    }
  };

  const handleAddAdmin = async () => {
    if (!newAdminId.trim() || !newAdminPassword) {
      Alert.alert("Missing fields", "Admin ID and password are required.");
      return;
    }
    try {
      await addAdminAccount(adminToken, newAdminId.trim(), newAdminPassword);
      setAdmins(await listAdminAccounts(adminToken));
      setNewAdminId("");
      setNewAdminPassword("");
    } catch (nextError) {
      Alert.alert("Add admin failed", nextError instanceof Error ? nextError.message : "Unexpected error");
    }
  };

  const handleRemoveAdmin = async (targetId: string) => {
    try {
      await removeAdminAccount(adminToken, targetId);
      setAdmins((current) => current.filter((entry) => entry !== targetId));
    } catch (nextError) {
      Alert.alert("Remove admin failed", nextError instanceof Error ? nextError.message : "Unexpected error");
    }
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.title}>Admin Console</Text>
          <Text style={styles.subtitle}>{adminId ? `Signed in as ${adminId}` : "Administrator"}</Text>
        </View>
        <Pressable style={styles.signOutButton} onPress={signOutAdmin}>
          <Text style={styles.signOutLabel}>Sign Out</Text>
        </Pressable>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabRow}>
        {(["overview", "students", "audits", "programs", "admins"] as Tab[]).map((tab) => (
          <Pressable
            key={tab}
            style={[styles.tabChip, activeTab === tab && styles.tabChipActive]}
            onPress={() => setActiveTab(tab)}
          >
            <Text style={[styles.tabLabel, activeTab === tab && styles.tabLabelActive]}>{tab.toUpperCase()}</Text>
          </Pressable>
        ))}
      </ScrollView>

      {loading ? (
        <View style={styles.screenCenter}>
          <ActivityIndicator color="#22D3EE" />
        </View>
      ) : error ? (
        <View style={styles.card}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      {!loading && !error && activeTab === "overview" && stats ? (
        <View style={styles.grid}>
          <View style={styles.card}><Text style={styles.label}>Students</Text><Text style={styles.metric}>{stats.total_students}</Text></View>
          <View style={styles.card}><Text style={styles.label}>Audits</Text><Text style={styles.metric}>{stats.total_audits}</Text></View>
          <View style={styles.card}><Text style={styles.label}>Today</Text><Text style={styles.metric}>{stats.audits_today}</Text></View>
          <View style={styles.cardWide}>
            <Text style={styles.label}>Latest Audit</Text>
            <Text style={styles.value}>{stats.latest_audit?.email || "No audits yet"}</Text>
            <Text style={styles.muted}>{stats.latest_audit?.created_at ? new Date(stats.latest_audit.created_at).toLocaleString() : ""}</Text>
          </View>
        </View>
      ) : null}

      {!loading && !error && activeTab === "students" ? (
        <View style={styles.section}>
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="Search students"
            placeholderTextColor="#64748B"
            style={styles.input}
          />
          {filteredStudents.map((student) => (
            <View key={student.id} style={styles.card}>
              <Text style={styles.value}>{student.full_name || student.student_id || student.email}</Text>
              <Text style={styles.muted}>{student.email}</Text>
              <Text style={styles.muted}>{student.program || "-"}{student.bba_concentration ? ` / ${student.bba_concentration}` : ""}</Text>
              <Text style={styles.muted}>Audits: {student.total_audits}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {!loading && !error && activeTab === "audits" ? (
        <View style={styles.section}>
          {audits.map((audit) => {
            const cgpa = typeof audit.level_2?.cgpa === "number" ? audit.level_2.cgpa.toFixed(2) : "-";
            const credits = audit.level_2?.credits_earned ?? audit.level_1?.credits_earned ?? audit.level_1?.total_earned ?? "-";
            const program = audit.level_1?.program || "-";
            const eligible = Boolean(audit.level_3?.eligible ?? audit.level_3?.is_eligible);
            return (
              <View key={audit.id} style={styles.card}>
                <Text style={styles.value}>{audit.email || "Unknown"}</Text>
                <Text style={styles.muted}>Program: {program}</Text>
                <Text style={styles.muted}>CGPA: {cgpa}</Text>
                <Text style={styles.muted}>Credits: {String(credits)}</Text>
                <Text style={[styles.muted, eligible ? styles.good : styles.bad]}>{eligible ? "Eligible" : "Ineligible"}</Text>
              </View>
            );
          })}
        </View>
      ) : null}

      {!loading && !error && activeTab === "programs" ? (
        <View style={styles.section}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabRow}>
            {programCodes.map((code) => (
              <Pressable key={code} style={[styles.tabChip, selectedProgramCode === code && styles.tabChipActive]} onPress={() => loadProgramEditor(programs, code)}>
                <Text style={[styles.tabLabel, selectedProgramCode === code && styles.tabLabelActive]}>{code}</Text>
              </Pressable>
            ))}
            <Pressable style={[styles.tabChip, selectedProgramCode === NEW_PROGRAM && styles.tabChipActive]} onPress={startNewProgram}>
              <Text style={[styles.tabLabel, selectedProgramCode === NEW_PROGRAM && styles.tabLabelActive]}>NEW</Text>
            </Pressable>
          </ScrollView>

          <TextInput value={programCodeInput} onChangeText={(value) => setProgramCodeInput(value.toUpperCase())} placeholder="Program code" placeholderTextColor="#64748B" style={styles.input} />
          {programRows.map((row, index) => (
            <View key={`${index}-${row.course_code}`} style={styles.card}>
              <TextInput value={row.course_code} onChangeText={(value) => setProgramRows((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, course_code: value.toUpperCase() } : item))} placeholder="Course code" placeholderTextColor="#64748B" style={styles.input} />
              <TextInput value={row.course_name} onChangeText={(value) => setProgramRows((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, course_name: value } : item))} placeholder="Course name" placeholderTextColor="#64748B" style={styles.input} />
              <TextInput value={row.credits} onChangeText={(value) => setProgramRows((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, credits: value } : item))} placeholder="Credits" placeholderTextColor="#64748B" keyboardType="number-pad" style={styles.input} />
              <TextInput value={row.category} onChangeText={(value) => setProgramRows((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, category: value } : item))} placeholder="Category" placeholderTextColor="#64748B" style={styles.input} />
              <Pressable style={styles.removeButton} onPress={() => setProgramRows((current) => current.filter((_, itemIndex) => itemIndex !== index))}>
                <Text style={styles.removeButtonLabel}>Remove Course</Text>
              </Pressable>
            </View>
          ))}
          <Pressable style={styles.secondaryButton} onPress={() => setProgramRows((current) => [...current, { course_code: "", course_name: "", credits: "3", category: "" }])}>
            <Text style={styles.secondaryButtonLabel}>Add Course Row</Text>
          </Pressable>
          <Pressable style={styles.primaryButton} onPress={saveProgram}>
            <Text style={styles.primaryButtonLabel}>Save Program</Text>
          </Pressable>
          {selectedProgramCode !== NEW_PROGRAM ? (
            <Pressable style={styles.removeButton} onPress={removeProgram}>
              <Text style={styles.removeButtonLabel}>Delete Program</Text>
            </Pressable>
          ) : null}
          {!!programMessage && <Text style={styles.muted}>{programMessage}</Text>}
        </View>
      ) : null}

      {!loading && !error && activeTab === "admins" ? (
        <View style={styles.section}>
          {admins.map((entry) => (
            <View key={entry} style={styles.cardRow}>
              <Text style={styles.value}>{entry}</Text>
              <Pressable style={styles.removeButtonSmall} onPress={() => handleRemoveAdmin(entry)}>
                <Text style={styles.removeButtonLabel}>Remove</Text>
              </Pressable>
            </View>
          ))}
          <View style={styles.card}>
            <TextInput value={newAdminId} onChangeText={setNewAdminId} placeholder="Admin ID" placeholderTextColor="#64748B" style={styles.input} />
            <TextInput value={newAdminPassword} onChangeText={setNewAdminPassword} placeholder="Password" placeholderTextColor="#64748B" secureTextEntry style={styles.input} />
            <Pressable style={styles.primaryButton} onPress={handleAddAdmin}>
              <Text style={styles.primaryButtonLabel}>Add Admin</Text>
            </Pressable>
          </View>
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#020617" },
  content: { padding: 16, gap: 12 },
  screenCenter: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#020617" },
  headerRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  title: { color: "#F8FAFC", fontSize: 26, fontWeight: "700" },
  subtitle: { color: "#94A3B8", marginTop: 4 },
  signOutButton: { backgroundColor: "#7F1D1D", borderRadius: 10, paddingHorizontal: 14, paddingVertical: 10 },
  signOutLabel: { color: "#FEE2E2", fontWeight: "700" },
  tabRow: { gap: 8, paddingVertical: 4 },
  tabChip: { borderRadius: 999, borderWidth: 1, borderColor: "#334155", paddingHorizontal: 12, paddingVertical: 8, backgroundColor: "#0F172A" },
  tabChipActive: { borderColor: "#22D3EE", backgroundColor: "#083344" },
  tabLabel: { color: "#94A3B8", fontWeight: "700", fontSize: 12 },
  tabLabelActive: { color: "#CFFAFE" },
  grid: { gap: 12 },
  section: { gap: 12 },
  card: { borderColor: "#1E293B", borderWidth: 1, borderRadius: 14, backgroundColor: "#0F172A", padding: 12, gap: 8 },
  cardWide: { borderColor: "#1E293B", borderWidth: 1, borderRadius: 14, backgroundColor: "#0F172A", padding: 12, gap: 8 },
  cardRow: { borderColor: "#1E293B", borderWidth: 1, borderRadius: 14, backgroundColor: "#0F172A", padding: 12, gap: 8, flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  label: { color: "#94A3B8", fontSize: 12, textTransform: "uppercase" },
  metric: { color: "#F8FAFC", fontSize: 28, fontWeight: "800" },
  value: { color: "#E2E8F0", fontSize: 16, fontWeight: "700" },
  muted: { color: "#94A3B8" },
  good: { color: "#67E8A4" },
  bad: { color: "#FDA4AF" },
  emptyText: { color: "#94A3B8" },
  errorText: { color: "#FCA5A5" },
  input: { backgroundColor: "#0B1220", borderColor: "#334155", borderWidth: 1, borderRadius: 10, color: "#E2E8F0", paddingHorizontal: 12, paddingVertical: 11 },
  primaryButton: { backgroundColor: "#22D3EE", borderRadius: 10, alignItems: "center", paddingVertical: 12 },
  primaryButtonLabel: { color: "#020617", fontWeight: "700" },
  secondaryButton: { borderRadius: 10, alignItems: "center", paddingVertical: 12, borderWidth: 1, borderColor: "#334155" },
  secondaryButtonLabel: { color: "#CBD5E1", fontWeight: "600" },
  removeButton: { backgroundColor: "#7F1D1D", borderRadius: 10, alignItems: "center", paddingVertical: 12 },
  removeButtonSmall: { backgroundColor: "#7F1D1D", borderRadius: 10, alignItems: "center", paddingHorizontal: 12, paddingVertical: 10 },
  removeButtonLabel: { color: "#FEE2E2", fontWeight: "700" },
});
