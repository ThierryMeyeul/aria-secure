import { useState, useEffect } from "react";
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert
} from "react-native";
import { useRouter, useLocalSearchParams } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import api from "../../services/api";

export default function PatientDetail() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const [patient, setPatient] = useState(null);
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchPatient();
    fetchImages();
  }, [id]);

  const fetchPatient = async () => {
    try {
      const res = await api.get(`/patients/${id}`);
      setPatient(res.data);
    } catch (e) {
      Alert.alert("Erreur", "Patient introuvable");
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const fetchImages = async () => {
    try {
      const res = await api.get(`/images?patient_id=${id}`);
      setImages(res.data.items || res.data || []);
    } catch (e) {
      console.log(e);
    }
  };

  const uploadImage = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission refusée", "Autorise l'accès à la galerie");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1,
    });

    if (result.canceled) return;

    const asset = result.assets[0];

    Alert.alert(
      "Partie du corps",
      "Quelle partie du corps ?",
      [
        { text: "Thorax", onPress: () => doUpload(asset, "chest") },
        { text: "Os/Fracture", onPress: () => doUpload(asset, "bone") },
        { text: "Autre", onPress: () => doUpload(asset, "other") },
        { text: "Annuler", style: "cancel" }
      ]
    );
  };

  const doUpload = async (asset, bodyPart) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("patient_id", id);
      formData.append("body_part", bodyPart);
      formData.append("image", {
        uri: asset.uri,
        type: "image/jpeg",
        name: "radio.jpg"
      });

      await api.post("/images/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      Alert.alert("✅ Succès", "Image uploadée avec succès !");
      fetchImages();
    } catch (e) {
      Alert.alert("Erreur", "Impossible d'uploader l'image");
      console.log(e);
    } finally {
      setUploading(false);
    }
  };

  const analyzeImage = async (imageId, type) => {
    Alert.alert(
      "Lancer l'analyse IA",
      `Analyser cette radio avec ${type === "chest" ? "CheXpert (thorax)" : "MURA (fractures)"} ?`,
      [
        { text: "Annuler", style: "cancel" },
        {
          text: "Analyser",
          onPress: async () => {
            try {
              const endpoint = type === "chest"
                ? `/analyze/chest?image_id=${imageId}`
                : `/analyze/fracture?image_id=${imageId}`;
              const res = await api.post(endpoint);
              Alert.alert(
                "🤖 Résultat IA",
                JSON.stringify(res.data, null, 2).slice(0, 500)
              );
            } catch (e) {
              Alert.alert("Erreur", "Analyse impossible pour le moment");
            }
          }
        }
      ]
    );
  };

  const getGenderLabel = (g) => g === "M" ? "Masculin" : g === "F" ? "Féminin" : "—";

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#1a73e8" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Text style={styles.backText}>‹ Retour</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Dossier patient</Text>
      </View>

      {/* Carte patient */}
      <View style={styles.card}>
        <View style={styles.avatarRow}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {patient?.first_name?.[0]}{patient?.last_name?.[0]}
            </Text>
          </View>
          <View>
            <Text style={styles.patientName}>
              {patient?.first_name} {patient?.last_name}
            </Text>
            <Text style={styles.patientSub}>
              Dossier #{patient?.medical_record_number}
            </Text>
          </View>
        </View>

        <View style={styles.divider} />

        <View style={styles.infoGrid}>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Date de naissance</Text>
            <Text style={styles.infoValue}>
              {patient?.date_of_birth
                ? new Date(patient.date_of_birth).toLocaleDateString("fr-FR")
                : "—"}
            </Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Genre</Text>
            <Text style={styles.infoValue}>{getGenderLabel(patient?.gender)}</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Téléphone</Text>
            <Text style={styles.infoValue}>{patient?.phone || "—"}</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Adresse</Text>
            <Text style={styles.infoValue}>{patient?.address || "—"}</Text>
          </View>
        </View>
      </View>

      {/* Section radiographies */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Radiographies</Text>
          <TouchableOpacity
            style={styles.uploadBtn}
            onPress={uploadImage}
            disabled={uploading}
          >
            {uploading
              ? <ActivityIndicator size="small" color="#fff" />
              : <Text style={styles.uploadBtnText}>+ Uploader</Text>
            }
          </TouchableOpacity>
        </View>

        {images.length === 0 ? (
          <View style={styles.emptyImages}>
            <Text style={styles.emptyIcon}>🩻</Text>
            <Text style={styles.emptyText}>Aucune radiographie</Text>
            <Text style={styles.emptySub}>Uploadez une radio pour lancer une analyse IA</Text>
          </View>
        ) : (
          images.map((img) => (
            <View key={img.id} style={styles.imageCard}>
              <View style={styles.imageInfo}>
                <Text style={styles.imageName}>🩻 {img.body_part || "Radio"}</Text>
                <Text style={styles.imageDate}>
                  {new Date(img.uploaded_at || img.created_at).toLocaleDateString("fr-FR")}
                </Text>
              </View>
              <View style={styles.imageActions}>
                <TouchableOpacity
                  style={[styles.analyzeBtn, { backgroundColor: "#e8f5e9" }]}
                  onPress={() => analyzeImage(img.id, "chest")}
                >
                  <Text style={[styles.analyzeBtnText, { color: "#2e7d32" }]}>Thorax</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.analyzeBtn, { backgroundColor: "#e3f2fd" }]}
                  onPress={() => analyzeImage(img.id, "fracture")}
                >
                  <Text style={[styles.analyzeBtnText, { color: "#1565c0" }]}>Fracture</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },

  header: {
    backgroundColor: "#fff", paddingHorizontal: 20,
    paddingTop: 56, paddingBottom: 16,
    borderBottomWidth: 0.5, borderBottomColor: "#e0e0e0"
  },
  backBtn: { marginBottom: 8 },
  backText: { fontSize: 16, color: "#1a73e8" },
  headerTitle: { fontSize: 22, fontWeight: "700", color: "#1a1a1a" },

  card: {
    backgroundColor: "#fff", margin: 16,
    borderRadius: 16, padding: 16,
    borderWidth: 0.5, borderColor: "#e8e8e8"
  },
  avatarRow: { flexDirection: "row", alignItems: "center", gap: 14, marginBottom: 16 },
  avatar: {
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: "#e8f0fe", justifyContent: "center", alignItems: "center"
  },
  avatarText: { fontSize: 20, fontWeight: "700", color: "#1a73e8" },
  patientName: { fontSize: 18, fontWeight: "700", color: "#1a1a1a" },
  patientSub: { fontSize: 13, color: "#888", marginTop: 2 },
  divider: { height: 0.5, backgroundColor: "#f0f0f0", marginBottom: 16 },

  infoGrid: { flexDirection: "row", flexWrap: "wrap", gap: 12 },
  infoItem: { width: "47%" },
  infoLabel: { fontSize: 11, color: "#999", marginBottom: 3, textTransform: "uppercase" },
  infoValue: { fontSize: 14, fontWeight: "500", color: "#1a1a1a" },

  section: {
    backgroundColor: "#fff", marginHorizontal: 16,
    borderRadius: 16, padding: 16,
    borderWidth: 0.5, borderColor: "#e8e8e8"
  },
  sectionHeader: {
    flexDirection: "row", justifyContent: "space-between",
    alignItems: "center", marginBottom: 16
  },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: "#1a1a1a" },
  uploadBtn: {
    backgroundColor: "#1a73e8", borderRadius: 20,
    paddingHorizontal: 14, paddingVertical: 7
  },
  uploadBtnText: { color: "#fff", fontSize: 13, fontWeight: "600" },

  emptyImages: { alignItems: "center", paddingVertical: 32 },
  emptyIcon: { fontSize: 40, marginBottom: 8 },
  emptyText: { fontSize: 15, fontWeight: "600", color: "#555" },
  emptySub: { fontSize: 12, color: "#999", marginTop: 4, textAlign: "center" },

  imageCard: {
    borderWidth: 0.5, borderColor: "#e8e8e8", borderRadius: 12,
    padding: 12, marginBottom: 10
  },
  imageInfo: { flexDirection: "row", justifyContent: "space-between", marginBottom: 10 },
  imageName: { fontSize: 14, fontWeight: "600", color: "#1a1a1a" },
  imageDate: { fontSize: 12, color: "#999" },
  imageActions: { flexDirection: "row", gap: 8 },
  analyzeBtn: { flex: 1, borderRadius: 8, paddingVertical: 8, alignItems: "center" },
  analyzeBtnText: { fontSize: 13, fontWeight: "600" },
});