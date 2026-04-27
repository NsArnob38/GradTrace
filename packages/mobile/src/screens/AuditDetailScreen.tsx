import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRoute } from "@react-navigation/native";
import type { RouteProp } from "@react-navigation/native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getAuditDetail, getTranscriptCourses, getTranscriptRawData, runAudit, updateTranscriptRawData } from "../lib/api";
import { generatePlannerPlans } from "../lib/mcp";
import type { RootStackParamList } from "../navigation/types";
import type { TranscriptCourseRow } from "../types/audit";

type PlannerKey = "fastest" | "balanced" | "cgpa";
type DetailTab = "roadmap" | "completed" | "mcp";

function parseCreditDeficit(requirements: string[]): number | null {
  const found = requirements.find((entry) => entry.startsWith("CREDIT_DEFICIT:"));
  if (!found) return null;
  const parsed = Number(found.split(":")[1]);
  return Number.isFinite(parsed) ? parsed : null;
}

export function AuditDetailScreen(): React.JSX.Element {
  const queryClient = useQueryClient();
  const route = useRoute<RouteProp<RootStackParamList, "AuditDetail">>();
  const transcriptId = route.params.transcriptId;
  const [maxCourses, setMaxCourses] = useState(5);
  const [maxCredits, setMaxCredits] = useState(15);
  const [plannerTab, setPlannerTab] = useState<PlannerKey>("balanced");
  const [detailTab, setDetailTab] = useState<DetailTab>("roadmap");
  const [completedRows, setCompletedRows] = useState<TranscriptCourseRow[]>([]);
  const [editingCompleted, setEditingCompleted] = useState(false);

  const detailQuery = useQuery({
    queryKey: ["audit-detail", transcriptId],
    queryFn: () => getAuditDetail(transcriptId),
  });

  const coursesQuery = useQuery({
    queryKey: ["transcript-courses", transcriptId],
    queryFn: () => getTranscriptCourses(transcriptId),
  });

  const rawRowsQuery = useQuery({
    queryKey: ["transcript-raw-rows", transcriptId],
    queryFn: () => getTranscriptRawData(transcriptId),
  });

  useEffect(() => {
    if (!editingCompleted && rawRowsQuery.data) {
      setCompletedRows(rawRowsQuery.data);
    }
  }, [editingCompleted, rawRowsQuery.data]);

  const plannerMutation = useMutation({
    mutationFn: async () => {
      const detail = detailQuery.data;
      const courses = coursesQuery.data;
      if (!detail || !courses) {
        throw new Error("Audit detail still loading");
      }

      const remaining = detail.level_3?.remaining ?? {};
      const remainingEntries = Object.entries(remaining).flatMap(([category, bucket]) =>
        Object.entries(bucket ?? {}).map(([courseCode, credits]) => ({
          category,
          course_code: courseCode.toUpperCase(),
          credits: Number(credits) || 3,
        }))
      );

      const coreCourses = remainingEntries
        .filter((entry) => entry.category.toLowerCase().includes("core"))
        .map((entry) => entry.course_code);

      const electivePool = remainingEntries
        .filter((entry) => entry.category.toLowerCase().includes("elective"))
        .map((entry) => entry.course_code);

      const totalCreditsRequired = detail.level_3?.total_credits_required ?? 130;
      const electiveCreditRequired = remainingEntries
        .filter((entry) => entry.category.toLowerCase().includes("elective"))
        .reduce((sum, entry) => sum + entry.credits, 0);

      const plans = await generatePlannerPlans({
        student_record: {
          student_id: transcriptId,
          courses,
        },
        program_requirements: {
          program_code: detail.meta?.program ?? "CSE",
          total_credits_required: totalCreditsRequired,
          core_courses_required: Array.from(new Set(coreCourses)),
          elective_credit_required: Math.round(Math.max(0, electiveCreditRequired)),
          elective_pool: Array.from(new Set(electivePool)),
        },
        available_courses: remainingEntries.map((entry) => ({
          course_code: entry.course_code,
          credits: Math.max(0, Math.min(12, Math.round(entry.credits))),
          category: entry.category.toLowerCase().includes("core")
            ? "CORE"
            : entry.category.toLowerCase().includes("elective")
            ? "ELECTIVE"
            : "GENERAL",
        })),
      }, { maxCourses, maxCredits });

      return plans;
    },
  });

  const saveCompletedMutation = useMutation({
    mutationFn: async () => {
      const sanitized = completedRows
        .map((row) => ({
          course_code: row.course_code.trim().toUpperCase(),
          course_name: (row.course_name || "").trim(),
          credits: Math.max(0, Math.min(12, Math.round(Number(row.credits) || 0))),
          grade: row.grade.trim().toUpperCase(),
          semester: (row.semester || "").trim(),
        }))
        .filter((row) => row.course_code && row.grade);

      if (sanitized.length === 0) {
        throw new Error("Please keep at least one valid course with code and grade.");
      }

      await updateTranscriptRawData(transcriptId, sanitized);
      await runAudit(
        transcriptId,
        detailQuery.data?.meta?.program === "BBA" ? "BBA" : "CSE",
        detailQuery.data?.meta?.concentration || undefined
      );
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["audit-detail", transcriptId] }),
        queryClient.invalidateQueries({ queryKey: ["transcript-courses", transcriptId] }),
        queryClient.invalidateQueries({ queryKey: ["transcript-raw-rows", transcriptId] }),
        queryClient.invalidateQueries({ queryKey: ["audit-history"] }),
      ]);
      setEditingCompleted(false);
      await Promise.all([detailQuery.refetch(), coursesQuery.refetch(), rawRowsQuery.refetch()]);
    },
  });

  const detail = detailQuery.data;
  const level1 = detail?.level_1 ?? {};
  const level2 = detail?.level_2 ?? {};
  const level3 = detail?.level_3 ?? {};
  const roadmap = detail?.roadmap ?? {};
  const plannerPlan = plannerMutation.data?.[plannerTab];
  const reasons = Array.isArray(level3.reasons) ? level3.reasons : [];
  const roadSteps = (roadmap.steps ?? []).slice(0, 10);

  const plannerStats = useMemo(() => {
    if (!plannerPlan) return { credits: 0, deficit: null as number | null, openRequirements: null as number | null };
    return {
      credits: plannerPlan.totalCredits,
      deficit: parseCreditDeficit(plannerPlan.remainingRequirements),
      openRequirements: plannerPlan.remainingRequirements.length,
    };
  }, [plannerPlan]);

  const completedStats = useMemo(() => {
    const courses = completedRows;
    const totalCredits = courses.reduce((sum, row) => sum + row.credits, 0);
    return {
      totalCourses: courses.length,
      totalCredits,
    };
  }, [completedRows]);

  const updateCompletedRow = (index: number, field: keyof TranscriptCourseRow, value: string) => {
    setCompletedRows((prev) => {
      const copy = [...prev];
      const row = copy[index];
      if (!row) return prev;
      if (field === "credits") {
        copy[index] = { ...row, credits: Number(value) || 0 };
      } else {
        copy[index] = { ...row, [field]: value };
      }
      return copy;
    });
  };

  const addCompletedRow = () => {
    setCompletedRows((prev) => [
      ...prev,
      {
        course_code: "",
        course_name: "",
        credits: 3,
        grade: "",
        semester: "",
      },
    ]);
  };

  const removeCompletedRow = (index: number) => {
    setCompletedRows((prev) => prev.filter((_, i) => i !== index));
  };

  if (detailQuery.isLoading || coursesQuery.isLoading || rawRowsQuery.isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#22D3EE" />
      </View>
    );
  }

  if (detailQuery.isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{detailQuery.error.message}</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <View style={styles.banner}>
        <View style={styles.bannerTop}>
          <Text style={styles.bannerTitle}>{level3.eligible ? "Eligible for Graduation" : "Not Yet Eligible"}</Text>
          <View style={[styles.bannerStatus, level3.eligible ? styles.bannerStatusOk : styles.bannerStatusWarn]}>
            <Text style={styles.bannerStatusText}>{level3.eligible ? "GRADUATED" : "ACTION REQUIRED"}</Text>
          </View>
        </View>
        <View style={styles.metricGrid}>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>CGPA</Text>
            <Text style={styles.metricValue}>{typeof level2.cgpa === "number" ? level2.cgpa.toFixed(2) : "0.00"}</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Credits</Text>
            <Text style={styles.metricValue}>{(level1.credits_earned ?? 0)}/{level3.total_credits_required ?? 130}</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Standing</Text>
            <Text style={styles.metricValue}>{level2.standing ?? "NORMAL"}</Text>
          </View>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Issues & Gaps</Text>
        {reasons.length > 0 ? (
          reasons.map((reason, index) => (
            <View key={`${index}-${reason}`} style={styles.issueRow}>
              <Ionicons name="warning-outline" size={16} color="#FCA5A5" />
              <Text style={styles.bodyText}>{reason}</Text>
            </View>
          ))
        ) : (
          <View style={styles.issueRow}>
            <Ionicons name="checkmark-circle-outline" size={16} color="#86EFAC" />
            <Text style={styles.bodyText}>No blocking issues listed.</Text>
          </View>
        )}
      </View>

      <View style={styles.segmentRow}>
        {([
          ["roadmap", "Roadmap"],
          ["completed", "Completed"],
          ["mcp", "Smart Planner"],
        ] as Array<[DetailTab, string]>).map(([key, label]) => (
          <Pressable
            key={key}
            style={[styles.segmentButton, detailTab === key && styles.segmentButtonActive]}
            onPress={() => setDetailTab(key)}
          >
            <Text style={[styles.segmentLabel, detailTab === key && styles.segmentLabelActive]}>{label}</Text>
          </Pressable>
        ))}
      </View>

      {detailTab === "roadmap" ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Roadmap</Text>
          <Text style={styles.caption}>Estimated semesters: {roadmap.estimated_semesters ?? 0}</Text>
          {roadSteps.map((step, idx) => (
            <View key={`${idx}-${step.action || "step"}`} style={styles.roadStep}>
              <View style={styles.roadIndexWrap}>
                <Text style={styles.roadIndex}>{idx + 1}</Text>
              </View>
              <View style={styles.roadTextWrap}>
                <Text style={styles.roadTitle}>{step.action ?? "Action"}</Text>
                {!!step.detail && <Text style={styles.roadDetail}>{step.detail}</Text>}
              </View>
            </View>
          ))}
        </View>
      ) : null}

      {detailTab === "completed" ? (
        <View style={styles.card}>
          <View style={styles.completedHeaderRow}>
            <Text style={styles.cardTitle}>Completed Courses</Text>
            <Pressable
              style={styles.secondaryButton}
              onPress={() => {
                if (editingCompleted) {
                  setEditingCompleted(false);
                  setCompletedRows(rawRowsQuery.data ?? []);
                } else {
                  setEditingCompleted(true);
                }
              }}
            >
              <Text style={styles.secondaryButtonLabel}>{editingCompleted ? "Cancel" : "Edit"}</Text>
            </Pressable>
          </View>

          <View style={styles.completedStatsRow}>
            <View style={styles.completedStatBox}>
              <Text style={styles.caption}>Courses</Text>
              <Text style={styles.completedStatValue}>{completedStats.totalCourses}</Text>
            </View>
            <View style={styles.completedStatBox}>
              <Text style={styles.caption}>Credits</Text>
              <Text style={styles.completedStatValue}>{completedStats.totalCredits}</Text>
            </View>
          </View>

          {completedRows.length > 0 ? (
            completedRows.map((course, index) => (
              <View key={`${course.course_code}-${index}`} style={styles.completedRow}>
                {editingCompleted ? (
                  <View style={styles.completedEditGrid}>
                    <TextInput
                      value={course.course_code}
                      onChangeText={(value) => updateCompletedRow(index, "course_code", value)}
                      autoCapitalize="characters"
                      style={styles.editInputCode}
                      placeholder="CSE115"
                      placeholderTextColor="#64748B"
                    />
                    <TextInput
                      value={course.course_name || ""}
                      onChangeText={(value) => updateCompletedRow(index, "course_name", value)}
                      style={styles.editInputName}
                      placeholder="Course name"
                      placeholderTextColor="#64748B"
                    />
                    <TextInput
                      value={String(course.credits)}
                      onChangeText={(value) => updateCompletedRow(index, "credits", value)}
                      keyboardType="numeric"
                      style={styles.editInputSmall}
                      placeholder="3"
                      placeholderTextColor="#64748B"
                    />
                    <TextInput
                      value={course.grade}
                      onChangeText={(value) => updateCompletedRow(index, "grade", value)}
                      autoCapitalize="characters"
                      style={styles.editInputSmall}
                      placeholder="A"
                      placeholderTextColor="#64748B"
                    />
                    <TextInput
                      value={course.semester || ""}
                      onChangeText={(value) => updateCompletedRow(index, "semester", value)}
                      style={styles.editInputSemester}
                      placeholder="Fall 2024"
                      placeholderTextColor="#64748B"
                    />
                    <Pressable style={styles.removeRowButton} onPress={() => removeCompletedRow(index)}>
                      <Ionicons name="trash-outline" size={16} color="#FCA5A5" />
                    </Pressable>
                  </View>
                ) : (
                  <>
                    <View>
                      <Text style={styles.completedCourseCode}>{course.course_code}</Text>
                      {!!course.course_name && <Text style={styles.completedName}>{course.course_name}</Text>}
                    </View>
                    <View style={styles.completedRight}>
                      <Text style={styles.completedGrade}>{course.grade}</Text>
                      <Text style={styles.completedCredits}>{course.credits} cr</Text>
                      {!!course.semester && <Text style={styles.completedCredits}>{course.semester}</Text>}
                    </View>
                  </>
                )}
              </View>
            ))
          ) : (
            <Text style={styles.bodyText}>No completed course data for this transcript yet.</Text>
          )}

          {editingCompleted ? (
            <View style={styles.completedActionsRow}>
              <Pressable style={styles.secondaryButton} onPress={addCompletedRow}>
                <Text style={styles.secondaryButtonLabel}>Add Course</Text>
              </Pressable>

              <Pressable
                style={[styles.runButton, saveCompletedMutation.isPending && styles.disabled]}
                disabled={saveCompletedMutation.isPending}
                onPress={() => saveCompletedMutation.mutate()}
              >
                {saveCompletedMutation.isPending ? (
                  <ActivityIndicator color="#020617" />
                ) : (
                  <Text style={styles.runLabel}>Save & Re-run Audit</Text>
                )}
              </Pressable>
            </View>
          ) : null}

          {saveCompletedMutation.isError ? (
            <Text style={styles.errorText}>{saveCompletedMutation.error.message}</Text>
          ) : null}
        </View>
      ) : null}

      {detailTab === "mcp" ? (
        <View style={styles.mcpCard}>
          <View style={styles.mcpTitleRow}>
            <Ionicons name="sparkles" size={16} color="#67E8F9" />
            <Text style={styles.cardTitle}>Smart Planner</Text>
          </View>
          <Text style={styles.caption}>
            {level3.eligible
              ? "No next-term plan is needed because this audit is already graduation eligible."
              : "Generate practical next-term plans using live MCP tools."}
          </Text>

          {level3.eligible ? (
            <View style={styles.completedPlannerBox}>
              <View style={styles.issueRowPlain}>
                <Ionicons name="checkmark-circle-outline" size={17} color="#86EFAC" />
                <Text style={styles.completedPlannerText}>Graduation requirements are already satisfied.</Text>
              </View>
              <Text style={styles.caption}>The planner is hidden for eligible audits so students do not receive unnecessary course recommendations.</Text>
            </View>
          ) : (
            <>
              <View style={styles.constraintsRow}>
                <View style={styles.constraintBox}>
                  <Text style={styles.constraintLabel}>Max Courses</Text>
                  <View style={styles.rowButtons}>
                    {[3, 4, 5, 6].map((num) => (
                      <Pressable
                        key={`courses-${num}`}
                        style={[styles.optionButton, maxCourses === num && styles.optionActive]}
                        onPress={() => setMaxCourses(num)}
                      >
                        <Text style={[styles.optionLabel, maxCourses === num && styles.optionLabelActive]}>{num}</Text>
                      </Pressable>
                    ))}
                  </View>
                </View>
                <View style={styles.constraintBox}>
                  <Text style={styles.constraintLabel}>Max Credits</Text>
                  <View style={styles.rowButtons}>
                    {[9, 12, 15, 18].map((num) => (
                      <Pressable
                        key={`credits-${num}`}
                        style={[styles.optionButton, maxCredits === num && styles.optionActive]}
                        onPress={() => setMaxCredits(num)}
                      >
                        <Text style={[styles.optionLabel, maxCredits === num && styles.optionLabelActive]}>{num}</Text>
                      </Pressable>
                    ))}
                  </View>
                </View>
              </View>

              <Pressable
                style={[styles.runButton, plannerMutation.isPending && styles.disabled]}
                disabled={plannerMutation.isPending}
                onPress={() => plannerMutation.mutate()}
              >
                {plannerMutation.isPending ? <ActivityIndicator color="#020617" /> : <Text style={styles.runLabel}>Generate Plans</Text>}
              </Pressable>

              {plannerMutation.isError && <Text style={styles.errorText}>{plannerMutation.error.message}</Text>}

              {plannerMutation.data && (
                <>
              <View style={styles.tabRow}>
                {([
                  ["fastest", "Fastest"],
                  ["balanced", "Balanced"],
                  ["cgpa", "CGPA"],
                ] as Array<[PlannerKey, string]>).map(([key, label]) => (
                  <Pressable
                    key={key}
                    style={[styles.tabButton, plannerTab === key && styles.tabButtonActive]}
                    onPress={() => setPlannerTab(key)}
                  >
                    <Text style={[styles.tabLabel, plannerTab === key && styles.tabLabelActive]}>{label}</Text>
                  </Pressable>
                ))}
              </View>

              {!!plannerPlan && (
                <View style={styles.planBox}>
                  <Text style={styles.planHeading}>{plannerTab.toUpperCase()} PLAN</Text>
                  <Text style={styles.caption}>{plannerPlan.rationale}</Text>
                  <View style={styles.courseWrap}>
                    {plannerPlan.courses.length > 0 ? (
                      plannerPlan.courses.map((course, index) => (
                        <View key={`${course}-${index}`} style={styles.courseChip}>
                          <Text style={styles.courseChipLabel}>{index + 1}. {course}</Text>
                        </View>
                      ))
                    ) : (
                      <Text style={styles.bodyText}>No courses selected for this strategy.</Text>
                    )}
                  </View>

                  <View style={styles.progressBox}>
                    <Text style={styles.progressLabel}>Next-term progress</Text>
                    <Text style={styles.progressText}>This plan adds {plannerStats.credits} planned credits and targets {plannerPlan.courses.length} roadmap item{plannerPlan.courses.length === 1 ? "" : "s"}.</Text>
                    <Text style={styles.caption}>This is a semester plan, not a promise that all graduation requirements finish immediately.</Text>
                  </View>

                  <View style={styles.planMetricGrid}>
                    <View style={styles.planMetricBox}>
                      <Text style={styles.constraintLabel}>Projected status</Text>
                      <Text style={[styles.planMetricValue, plannerPlan.eligibleAfter ? styles.successText : styles.warningText]}>
                        {plannerPlan.eligibleAfter ? "Eligible after this plan" : "Not eligible after this term"}
                      </Text>
                    </View>
                    <View style={styles.planMetricBox}>
                      <Text style={styles.constraintLabel}>After this term</Text>
                      <Text style={styles.planMetricValue}>{plannerStats.openRequirements === 0 ? "All cleared" : `${plannerStats.openRequirements ?? "Unknown"} still open`}</Text>
                    </View>
                  </View>

                  <View style={styles.longTermBox}>
                    <Text style={styles.constraintLabel}>Long-term graduation context</Text>
                    <Text style={styles.bodyText}>{plannerStats.deficit === null ? "Credit gap unknown" : `${plannerStats.deficit} credits still needed`}</Text>
                    <Text style={styles.caption}>This is the remaining program-wide gap after this semester plan. Future terms are still expected.</Text>
                  </View>
                </View>
              )}
                </>
              )}
            </>
          )}
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#020617" },
  content: { padding: 14, gap: 10, paddingBottom: 36 },
  center: { flex: 1, backgroundColor: "#020617", alignItems: "center", justifyContent: "center" },
  errorText: { color: "#FCA5A5", marginTop: 8 },
  banner: {
    backgroundColor: "#0A2746",
    borderRadius: 16,
    borderColor: "#1C5E8E",
    borderWidth: 1,
    padding: 13,
  },
  bannerTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 10, gap: 8 },
  bannerTitle: { color: "#E0F2FE", fontWeight: "800", fontSize: 20, flex: 1 },
  bannerStatus: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 5, borderWidth: 1 },
  bannerStatusOk: { borderColor: "#14532D", backgroundColor: "#052E16" },
  bannerStatusWarn: { borderColor: "#7F1D1D", backgroundColor: "#450A0A" },
  bannerStatusText: { color: "#DCFCE7", fontSize: 11, fontWeight: "700" },
  metricGrid: { flexDirection: "row", gap: 8 },
  metricCard: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#1E4D78",
    backgroundColor: "#09203A",
    padding: 9,
  },
  metricLabel: { color: "#8FB9DA", fontSize: 11, textTransform: "uppercase", marginBottom: 3 },
  metricValue: { color: "#E0F2FE", fontWeight: "800", fontSize: 15 },
  card: {
    backgroundColor: "#091833",
    borderWidth: 1,
    borderColor: "#16325B",
    borderRadius: 16,
    padding: 12,
    gap: 8,
  },
  mcpCard: {
    backgroundColor: "#071E2E",
    borderWidth: 1,
    borderColor: "#145C76",
    borderRadius: 16,
    padding: 12,
    gap: 8,
  },
  mcpTitleRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  cardTitle: { color: "#F8FAFC", fontWeight: "800", fontSize: 21 },
  caption: { color: "#9BB0CC", fontSize: 12 },
  bodyText: { color: "#CBD5E1", fontSize: 13, flex: 1 },
  issueRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    backgroundColor: "#071429",
    borderWidth: 1,
    borderColor: "#183760",
    borderRadius: 12,
    padding: 9,
  },
  issueRowPlain: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  segmentRow: { flexDirection: "row", gap: 8 },
  segmentButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#1D4B7D",
    borderRadius: 10,
    backgroundColor: "#071429",
    alignItems: "center",
    paddingVertical: 10,
  },
  segmentButtonActive: {
    backgroundColor: "#0E7490",
    borderColor: "#67E8F9",
  },
  segmentLabel: { color: "#A7BCD8", fontWeight: "700", fontSize: 12 },
  segmentLabelActive: { color: "#ECFEFF" },
  roadStep: {
    flexDirection: "row",
    borderWidth: 1,
    borderColor: "#17335A",
    borderRadius: 12,
    backgroundColor: "#071429",
    padding: 10,
    gap: 10,
  },
  roadIndexWrap: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#103A67",
  },
  roadIndex: { color: "#BAE6FD", fontWeight: "800", fontSize: 12 },
  roadTextWrap: { flex: 1 },
  roadTitle: { color: "#E2E8F0", fontWeight: "700" },
  roadDetail: { color: "#9BB0CC", marginTop: 2, lineHeight: 20 },
  completedStatsRow: { flexDirection: "row", gap: 8 },
  completedHeaderRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8 },
  completedStatBox: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#1D4B7D",
    borderRadius: 12,
    backgroundColor: "#071429",
    padding: 10,
  },
  completedStatValue: { color: "#E2E8F0", fontWeight: "800", fontSize: 24 },
  completedRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#17335A",
    borderRadius: 12,
    backgroundColor: "#071429",
    padding: 10,
  },
  completedCourseCode: { color: "#E2E8F0", fontWeight: "700", letterSpacing: 0.4 },
  completedName: { color: "#9BB0CC", marginTop: 3, maxWidth: 210 },
  completedRight: { alignItems: "flex-end" },
  completedGrade: { color: "#67E8F9", fontWeight: "800" },
  completedCredits: { color: "#9BB0CC", fontSize: 12 },
  completedEditGrid: {
    width: "100%",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 7,
    alignItems: "center",
  },
  editInputCode: {
    width: 92,
    borderWidth: 1,
    borderColor: "#2A5B89",
    backgroundColor: "#081726",
    color: "#E2E8F0",
    borderRadius: 8,
    paddingHorizontal: 9,
    paddingVertical: 7,
  },
  editInputName: {
    flex: 1,
    minWidth: 130,
    borderWidth: 1,
    borderColor: "#2A5B89",
    backgroundColor: "#081726",
    color: "#E2E8F0",
    borderRadius: 8,
    paddingHorizontal: 9,
    paddingVertical: 7,
  },
  editInputSmall: {
    width: 62,
    borderWidth: 1,
    borderColor: "#2A5B89",
    backgroundColor: "#081726",
    color: "#E2E8F0",
    borderRadius: 8,
    paddingHorizontal: 9,
    paddingVertical: 7,
  },
  editInputSemester: {
    flex: 1,
    minWidth: 120,
    borderWidth: 1,
    borderColor: "#2A5B89",
    backgroundColor: "#081726",
    color: "#E2E8F0",
    borderRadius: 8,
    paddingHorizontal: 9,
    paddingVertical: 7,
  },
  removeRowButton: {
    width: 30,
    height: 30,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#7F1D1D",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#3A0A0A",
  },
  completedActionsRow: {
    marginTop: 8,
    flexDirection: "row",
    gap: 8,
    alignItems: "center",
  },
  secondaryButton: {
    borderWidth: 1,
    borderColor: "#2A5B89",
    backgroundColor: "#0B1A33",
    borderRadius: 9,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  secondaryButtonLabel: {
    color: "#CFE9FF",
    fontWeight: "700",
    fontSize: 12,
  },
  constraintsRow: { gap: 10 },
  constraintBox: { backgroundColor: "#081726", borderRadius: 10, borderWidth: 1, borderColor: "#215072", padding: 8 },
  constraintLabel: { color: "#94A3B8", fontSize: 11, textTransform: "uppercase", marginBottom: 8 },
  rowButtons: { flexDirection: "row", gap: 6, flexWrap: "wrap" },
  optionButton: {
    borderWidth: 1,
    borderColor: "#334155",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  optionActive: { backgroundColor: "#0E7490", borderColor: "#22D3EE" },
  optionLabel: { color: "#CBD5E1", fontWeight: "600" },
  optionLabelActive: { color: "#ECFEFF" },
  runButton: {
    marginTop: 4,
    backgroundColor: "#22D3EE",
    borderRadius: 10,
    alignItems: "center",
    paddingVertical: 12,
  },
  disabled: { opacity: 0.6 },
  runLabel: { color: "#020617", fontWeight: "700" },
  tabRow: { marginTop: 10, flexDirection: "row", gap: 8 },
  tabButton: {
    borderWidth: 1,
    borderColor: "#334155",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  tabButtonActive: { backgroundColor: "#0E7490", borderColor: "#22D3EE" },
  tabLabel: { color: "#CBD5E1", fontWeight: "600" },
  tabLabelActive: { color: "#ECFEFF" },
  planBox: { marginTop: 10, borderWidth: 1, borderColor: "#2A6685", borderRadius: 12, padding: 10, gap: 6, backgroundColor: "#082032" },
  planHeading: { color: "#E2E8F0", fontWeight: "700" },
  completedPlannerBox: {
    borderWidth: 1,
    borderColor: "#14532D",
    backgroundColor: "#052E16",
    borderRadius: 12,
    padding: 10,
    gap: 6,
  },
  completedPlannerText: { color: "#DCFCE7", fontWeight: "800", flex: 1 },
  progressBox: {
    borderWidth: 1,
    borderColor: "#8A6D1D",
    backgroundColor: "#25271F",
    borderRadius: 10,
    padding: 9,
    gap: 3,
  },
  progressLabel: { color: "#FACC15", fontSize: 11, textTransform: "uppercase", fontWeight: "800" },
  progressText: { color: "#F8FAFC", fontSize: 13, fontWeight: "800" },
  planMetricGrid: { flexDirection: "row", gap: 8 },
  planMetricBox: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#2A5B89",
    borderRadius: 10,
    backgroundColor: "#071429",
    padding: 9,
  },
  planMetricValue: { color: "#E2E8F0", fontSize: 13, fontWeight: "800" },
  successText: { color: "#86EFAC" },
  warningText: { color: "#FACC15" },
  longTermBox: {
    borderWidth: 1,
    borderColor: "#203859",
    borderRadius: 10,
    backgroundColor: "#081426",
    padding: 9,
    gap: 2,
  },
  courseWrap: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  courseChip: {
    borderWidth: 1,
    borderColor: "#334155",
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: "#0B1220",
  },
  courseChipLabel: { color: "#CFFAFE", fontSize: 12 },
});
