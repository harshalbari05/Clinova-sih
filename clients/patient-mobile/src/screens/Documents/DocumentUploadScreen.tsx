import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';
import { NavigationProp, ScreenRouteProp } from '../../navigation/types';
import { documentApi } from '../../api';
import { MedicalDocument } from '../../types';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Button from '../../components/Button';
import StepIndicator from '../../components/StepIndicator';

const DOCUMENT_TYPES = [
  { id: 'prescription', label: 'Prescription', icon: 'medical-outline' },
  { id: 'lab_report', label: 'Lab Report', icon: 'flask-outline' },
  { id: 'discharge_summary', label: 'Discharge Summary', icon: 'clipboard-outline' },
  { id: 'radiology_scan', label: 'Radiology / Scan', icon: 'scan-outline' },
  { id: 'other', label: 'Other Document', icon: 'document-outline' },
];

export const DocumentUploadScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'DocumentUpload'>>();
  const route = useRoute<ScreenRouteProp<'DocumentUpload'>>();
  const consultationId = route.params?.consultationId;

  const [selectedDocType, setSelectedDocType] = useState('prescription');
  const [selectedFile, setSelectedFile] = useState<{
    uri: string;
    name: string;
    type: string;
    previewUri?: string;
  } | null>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<MedicalDocument | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 1. Camera Capture
  const handleCameraCapture = async () => {
    try {
      setError(null);
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        setError('Camera permission is required to capture documents.');
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.85,
        allowsEditing: true,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        const asset = result.assets[0];
        setSelectedFile({
          uri: asset.uri,
          name: `camera_doc_${Date.now()}.jpg`,
          type: 'image/jpeg',
          previewUri: asset.uri,
        });
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to capture image.');
    }
  };

  // 2. Photo Gallery Selection
  const handleGalleryPick = async () => {
    try {
      setError(null);
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        setError('Gallery permission is required to select images.');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.85,
        allowsEditing: true,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        const asset = result.assets[0];
        setSelectedFile({
          uri: asset.uri,
          name: asset.fileName || `gallery_doc_${Date.now()}.jpg`,
          type: asset.mimeType || 'image/jpeg',
          previewUri: asset.uri,
        });
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to select image.');
    }
  };

  // 3. Document / PDF Picker
  const handleDocumentPick = async () => {
    try {
      setError(null);
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/*'],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        const asset = result.assets[0];
        setSelectedFile({
          uri: asset.uri,
          name: asset.name,
          type: asset.mimeType || 'application/pdf',
          previewUri: asset.mimeType?.startsWith('image/') ? asset.uri : undefined,
        });
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to pick document.');
    }
  };

  // 4. Upload to existing backend endpoint
  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setError(null);

      const doc = await documentApi.uploadDocument(
        selectedFile,
        selectedDocType,
        consultationId
      );

      setUploadSuccess(doc);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Document upload failed. Please try again.';
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Header
        title="Upload Medical Document"
        onBack={() => navigation.goBack()}
        rightAction={
          <TouchableOpacity
            onPress={() => navigation.navigate('DocumentList', { consultationId })}
            style={styles.listHeaderBtn}
          >
            <Ionicons name="folder-outline" size={20} color={colors.primary} />
          </TouchableOpacity>
        }
      />
      {consultationId && <StepIndicator currentStep={5} />}

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Document Classification */}
        <Text style={styles.sectionTitle}>1. Select Document Type</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.docTypeRow}>
          {DOCUMENT_TYPES.map((t) => {
            const isSelected = selectedDocType === t.id;
            return (
              <TouchableOpacity
                key={t.id}
                style={[styles.docTypeChip, isSelected && styles.docTypeChipSelected]}
                onPress={() => setSelectedDocType(t.id)}
              >
                <Ionicons
                  name={t.icon as any}
                  size={16}
                  color={isSelected ? colors.onPrimary : colors.primary}
                />
                <Text style={[styles.docTypeLabel, isSelected && styles.docTypeLabelSelected]}>
                  {t.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* Source Selection Buttons */}
        <Text style={styles.sectionTitle}>2. Choose Upload Source</Text>
        <View style={styles.sourceGrid}>
          <TouchableOpacity
            style={styles.sourceBtn}
            activeOpacity={0.75}
            onPress={handleCameraCapture}
          >
            <View style={styles.sourceIconCircle}>
              <Ionicons name="camera" size={24} color={colors.primary} />
            </View>
            <Text style={styles.sourceBtnTitle}>Take Photo</Text>
            <Text style={styles.sourceBtnSub}>Capture with camera</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.sourceBtn}
            activeOpacity={0.75}
            onPress={handleGalleryPick}
          >
            <View style={styles.sourceIconCircle}>
              <Ionicons name="images" size={24} color={colors.primary} />
            </View>
            <Text style={styles.sourceBtnTitle}>Photo Library</Text>
            <Text style={styles.sourceBtnSub}>Choose from gallery</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.sourceBtn}
            activeOpacity={0.75}
            onPress={handleDocumentPick}
          >
            <View style={styles.sourceIconCircle}>
              <Ionicons name="document-attach" size={24} color={colors.primary} />
            </View>
            <Text style={styles.sourceBtnTitle}>Browse PDF / Files</Text>
            <Text style={styles.sourceBtnSub}>PDF or document file</Text>
          </TouchableOpacity>
        </View>

        {/* Error message */}
        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorBoxText}>{error}</Text>
          </View>
        )}

        {/* Selected File Preview Card */}
        {selectedFile && (
          <Card elevated style={styles.previewCard}>
            <Text style={styles.previewHeading}>Selected Document</Text>
            {selectedFile.previewUri ? (
              <Image source={{ uri: selectedFile.previewUri }} style={styles.previewImage} resizeMode="contain" />
            ) : (
              <View style={styles.pdfPlaceholder}>
                <Ionicons name="document-text" size={48} color={colors.primary} />
                <Text style={styles.pdfFilename}>{selectedFile.name}</Text>
              </View>
            )}

            <View style={styles.fileDetailsRow}>
              <Text style={styles.fileNameText} numberOfLines={1}>
                {selectedFile.name}
              </Text>
              <TouchableOpacity onPress={() => setSelectedFile(null)}>
                <Text style={styles.removeText}>Remove</Text>
              </TouchableOpacity>
            </View>

            <Button
              title="Upload & Run OCR Extraction"
              onPress={handleUpload}
              loading={uploading}
              style={{ marginTop: spacing.md }}
            />
          </Card>
        )}

        {/* Upload Success Card */}
        {uploadSuccess && (
          <Card elevated style={styles.successCard}>
            <Ionicons name="checkmark-circle" size={36} color={colors.verified} />
            <Text style={styles.successTitle}>Upload Successful!</Text>
            <Text style={styles.successSubtitle}>
              Document persisted and queued for OCR structured extraction.
            </Text>

            <View style={styles.successActions}>
              <Button
                title="View Extraction Results"
                onPress={() =>
                  navigation.navigate('DocumentExtraction', { documentId: uploadSuccess.id })
                }
                variant="secondary"
                style={{ flex: 1, marginRight: spacing.xs }}
              />
              <Button
                title="Upload Another"
                onPress={() => {
                  setSelectedFile(null);
                  setUploadSuccess(null);
                }}
                variant="outline"
                style={{ flex: 1, marginLeft: spacing.xs }}
              />
            </View>

            {consultationId && (
              <Button
                title="Continue to Clinical Summary →"
                onPress={() => navigation.navigate('ClinicalSummary', { consultationId })}
                style={{ marginTop: spacing.sm, width: '100%' }}
              />
            )}
          </Card>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  listHeaderBtn: {
    padding: spacing.xs,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.onSurface,
    marginBottom: spacing.xs,
  },
  docTypeRow: {
    flexDirection: 'row',
    marginBottom: spacing.lg,
  },
  docTypeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: spacing.sm,
  },
  docTypeChipSelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  docTypeLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.primary,
    marginLeft: 6,
  },
  docTypeLabelSelected: {
    color: colors.onPrimary,
  },
  sourceGrid: {
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  sourceBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.cardBg,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sourceIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.secondaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  sourceBtnTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.onSurface,
  },
  sourceBtnSub: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  errorBox: {
    backgroundColor: colors.errorContainer,
    padding: spacing.md,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.md,
  },
  errorBoxText: {
    color: colors.error,
    fontSize: 13,
    fontWeight: '500',
  },
  previewCard: {
    marginBottom: spacing.lg,
  },
  previewHeading: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.onSurface,
    marginBottom: spacing.sm,
  },
  previewImage: {
    width: '100%',
    height: 200,
    backgroundColor: '#F1F5F9',
    borderRadius: borderRadius.md,
  },
  pdfPlaceholder: {
    width: '100%',
    height: 140,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.md,
  },
  pdfFilename: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.onSurface,
    marginTop: spacing.xs,
  },
  fileDetailsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  fileNameText: {
    fontSize: 13,
    color: colors.textSecondary,
    flex: 1,
  },
  removeText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.error,
    marginLeft: spacing.sm,
  },
  successCard: {
    alignItems: 'center',
    padding: spacing.lg,
    backgroundColor: '#F0FDF4',
    borderColor: '#86EFAC',
  },
  successTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#166534',
    marginTop: spacing.xs,
  },
  successSubtitle: {
    fontSize: 13,
    color: '#15803D',
    textAlign: 'center',
    marginTop: 4,
    marginBottom: spacing.md,
    lineHeight: 18,
  },
  successActions: {
    flexDirection: 'row',
    width: '100%',
  },
});

export default DocumentUploadScreen;
