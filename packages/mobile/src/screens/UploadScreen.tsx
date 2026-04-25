import React, { useMemo, useState } from "react";
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
import * as DocumentPicker from "expo-document-picker";
import * as ImagePicker from "expo-image-picker";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { runAudit, uploadTranscript } from "../lib/api";
import type { RootStackParamList } from "../navigation/types";
import type { UploadFileAsset } from "../types/audit";

const ACCEPTED = ["image/jpeg", "image/png", "image/webp", "application/pdf", "text/csv"];
const MAX_MB = 12;

export function UploadScreen(): React.JSX.Element {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<UploadFileAsset | null>(null);
  const [program, setProgram] = useState<"CSE" | "BBA">("CSE");
  const [concentration, setConcentration] = useState("");

  const uploadMutation = useMutation({
    mutationFn: async (asset: UploadFileAsset) => {
      const uploaded = await uploadTranscript(asset);
      await runAudit(uploaded.id, program, program === "BBA" ? concentration : undefined);
      return uploaded.id;
    },
    onSuccess: async (transcriptId) => {
      await queryClient.invalidateQueries({ queryKey: ["audit-history"] });
      navigation.navigate("AuditDetail", { transcriptId });
    },
    onError: (error) => {
      Alert.alert("Upload failed", error instanceof Error ? error.message : "Unexpected error");
    },
  });

  const selectedLabel = useMemo(() => {
    if (!selectedFile) return "No file selected";
    const mb = (selectedFile.sizeBytes / (1024 * 1024)).toFixed(2);
    return `${selectedFile.name} (${mb} MB)`;
  }, [selectedFile]);

  const validateAsset = (asset: UploadFileAsset): UploadFileAsset | null => {
    const lowerName = asset.name.toLowerCase();
    const fallbackMime = lowerName.endsWith(".pdf")
      ? "application/pdf"
      : lowerName.endsWith(".csv")
      ? "text/csv"
      : lowerName.endsWith(".jpg") || lowerName.endsWith(".jpeg")
      ? "image/jpeg"
      : lowerName.endsWith(".png")
      ? "image/png"
      : lowerName.endsWith(".webp")
      ? "image/webp"
      : asset.mimeType;

    if (!ACCEPTED.includes(fallbackMime)) {
      Alert.alert("Unsupported file", "Use JPG, PNG, WEBP, PDF, or CSV only.");
      return null;
    }

    const maxBytes = MAX_MB * 1024 * 1024;
    if (asset.sizeBytes > maxBytes) {
      Alert.alert("File too large", `Maximum file size is ${MAX_MB} MB.`);
      return null;
    }

    return { ...asset, mimeType: fallbackMime };
  };

  const pickDocument = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      copyToCacheDirectory: true,
      type: ["application/pdf", "text/csv", "image/*"],
    });
    if (result.canceled || result.assets.length === 0) return;
    const asset = result.assets[0];
    if (!asset) return;
    const candidate: UploadFileAsset = {
      uri: asset.uri,
      name: asset.name,
      mimeType: asset.mimeType || "application/octet-stream",
      sizeBytes: asset.size || 0,
    };
    const validated = validateAsset(candidate);
    if (validated) setSelectedFile(validated);
  };

  const pickFromGallery = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission required", "Allow photo access to upload transcript images.");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
    });
    if (result.canceled || result.assets.length === 0) return;
    const asset = result.assets[0];
    if (!asset) return;
    const candidate: UploadFileAsset = {
      uri: asset.uri,
      name: asset.fileName || `photo-${Date.now()}.jpg`,
      mimeType: asset.mimeType || "image/jpeg",
      sizeBytes: asset.fileSize || 0,
    };
    const validated = validateAsset(candidate);
    if (validated) setSelectedFile(validated);
  };

  const pickFromCamera = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission required", "Allow camera access to capture transcript images.");
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
    });
    if (result.canceled || result.assets.length === 0) return;
    const asset = result.assets[0];
    if (!asset) return;
    const candidate: UploadFileAsset = {
      uri: asset.uri,
      name: asset.fileName || `camera-${Date.now()}.jpg`,
      mimeType: asset.mimeType || "image/jpeg",
      sizeBytes: asset.fileSize || 0,
    };
    const validated = validateAsset(candidate);
    if (validated) setSelectedFile(validated);
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Text style={styles.heading}>Upload Transcript</Text>
      <Text style={styles.subheading}>Pick PDF/CSV or photo and run a real audit.</Text>

      <View style={styles.card}>
        <Text style={styles.label}>Program</Text>
        <View style={styles.row}>
          <Pressable style={[styles.toggle, program === "CSE" && styles.toggleActive]} onPress={() => setProgram("CSE")}>
            <Text style={[styles.toggleLabel, program === "CSE" && styles.toggleLabelActive]}>CSE</Text>
          </Pressable>
          <Pressable style={[styles.toggle, program === "BBA" && styles.toggleActive]} onPress={() => setProgram("BBA")}>
            <Text style={[styles.toggleLabel, program === "BBA" && styles.toggleLabelActive]}>BBA</Text>
          </Pressable>
        </View>

        {program === "BBA" && (
          <>
            <Text style={styles.label}>Concentration (optional)</Text>
            <TextInput
              value={concentration}
              onChangeText={setConcentration}
              placeholder="e.g. FIN"
              autoCapitalize="characters"
              placeholderTextColor="#64748B"
              style={styles.input}
            />
          </>
        )}

        <Text style={styles.label}>Selected</Text>
        <Text style={styles.fileLabel}>{selectedLabel}</Text>

        <View style={styles.rowWrap}>
          <Pressable style={styles.actionButton} onPress={pickFromCamera}>
            <Text style={styles.actionLabel}>Take Photo</Text>
          </Pressable>
          <Pressable style={styles.actionButton} onPress={pickFromGallery}>
            <Text style={styles.actionLabel}>Choose Photo</Text>
          </Pressable>
          <Pressable style={styles.actionButton} onPress={pickDocument}>
            <Text style={styles.actionLabel}>Pick File</Text>
          </Pressable>
        </View>

        <Pressable
          style={[styles.uploadButton, (!selectedFile || uploadMutation.isPending) && styles.disabledButton]}
          disabled={!selectedFile || uploadMutation.isPending}
          onPress={() => selectedFile && uploadMutation.mutate(selectedFile)}
        >
          {uploadMutation.isPending ? (
            <ActivityIndicator color="#020617" />
          ) : (
            <Text style={styles.uploadLabel}>Upload & Run Audit</Text>
          )}
        </Pressable>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: "#020617" },
  content: { padding: 14, gap: 10 },
  heading: { color: "#F8FAFC", fontSize: 24, fontWeight: "700" },
  subheading: { color: "#94A3B8", marginBottom: 6 },
  card: {
    backgroundColor: "#0F172A",
    borderWidth: 1,
    borderColor: "#1E293B",
    borderRadius: 14,
    padding: 12,
    gap: 10,
  },
  label: { color: "#94A3B8", fontSize: 12, textTransform: "uppercase" },
  row: { flexDirection: "row", gap: 8 },
  rowWrap: { flexDirection: "row", gap: 8, flexWrap: "wrap" },
  toggle: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#334155",
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: "center",
  },
  toggleActive: { backgroundColor: "#0E7490", borderColor: "#22D3EE" },
  toggleLabel: { color: "#CBD5E1", fontWeight: "600" },
  toggleLabelActive: { color: "#ECFEFF" },
  input: {
    borderWidth: 1,
    borderColor: "#334155",
    borderRadius: 10,
    color: "#E2E8F0",
    backgroundColor: "#0B1220",
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  fileLabel: { color: "#CBD5E1" },
  actionButton: {
    backgroundColor: "#1E293B",
    borderRadius: 9,
    paddingHorizontal: 10,
    paddingVertical: 10,
  },
  actionLabel: { color: "#E2E8F0", fontWeight: "600" },
  uploadButton: {
    marginTop: 6,
    backgroundColor: "#22D3EE",
    borderRadius: 10,
    alignItems: "center",
    paddingVertical: 12,
  },
  disabledButton: { opacity: 0.5 },
  uploadLabel: { color: "#020617", fontWeight: "700" },
});
