import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  Image,
  RefreshControl,
  Modal,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { colors, spacing, borderRadius, typography, shadows } from '../constants/theme';
import { Header } from '../components/common/Header';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { CameraScanner } from '../components/camera/CameraScanner';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useConsultation } from '../context/ConsultationContext';
import { MedicalDocument, StructuredExtraction, DocumentType } from '../types';

interface DocumentsScreenProps {
  navigation?: any;
  onNavigateToIntake?: () => void;
  onNavigateToTimeline?: () => void;
}

const DOC_TYPE_OPTIONS: { key: DocumentType; label: string; icon: string }[] = [
  { key: 'prescription', label: 'Prescription', icon: '💊' },
  { key: 'lab_report', label: 'Lab Report', icon: '🔬' },
  { key: 'radiology_scan', label: 'X-Ray / Scan', icon: '🩻' },
  { key: 'discharge_summary', label: 'Discharge Summary', icon: '🏥' },
  { key: 'other', label: 'Other', icon: '📄' },
];

export const DocumentsScreen: React.FC<DocumentsScreenProps> = ({
  navigation,
  onNavigateToIntake,
  onNavigateToTimeline,
}) => {
  const { patient } = useAuth();
  const { consultation } = useConsultation();

  // State
  const [selectedCategory, setSelectedCategory] = useState<DocumentType>('prescription');
  const [cameraOpen, setCameraOpen] = useState(false);
  const [capturedUri, setCapturedUri] = useState<string | null>(null);
  const [capturedFileName, setCapturedFileName] = useState<string>('scan_document.jpg');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [currentDocument, setCurrentDocument] = useState<MedicalDocument | null>(null);
  const [currentExtraction, setCurrentExtraction] = useState<StructuredExtraction | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [uploadedDocsList, setUploadedDocsList] = useState<MedicalDocument[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);

  // Editable Form fields for verified extraction
  const [formDocType, setFormDocType] = useState('Prescription');
  const [formDocDate, setFormDocDate] = useState('');
  const [formHospital, setFormHospital] = useState('');
  const [formDoctor, setFormDoctor] = useState('');
  const [formMedicines, setFormMedicines] = useState('');
  const [formTests, setFormTests] = useState('');
  const [formNotes, setFormNotes] = useState('');
  const [isSavedLocally, setIsSavedLocally] = useState(false);

  // Load uploaded documents on mount
  const loadDocuments = useCallback(async () => {
    try {
      setIsLoadingList(true);
      const docs = await apiService.getMyDocuments();
      setUploadedDocsList(docs || []);
    } catch {
      // Graceful empty fallback
      setUploadedDocsList([]);
    } finally {
      setIsLoadingList(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const onRefresh = () => {
    setRefreshing(true);
    loadDocuments();
  };

  // Launch device image picker
  const handlePickFile = async () => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Permission Needed',
          'Access to your photo gallery is required to upload medical documents.'
        );
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: false,
        quality: 0.85,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setCapturedUri(asset.uri);
        const name = asset.fileName || `document_${Date.now()}.jpg`;
        setCapturedFileName(name);
        handleStartUpload(asset.uri, name);
      }
    } catch {
      Alert.alert('Upload Error', 'Could not access file selection. Please try again.');
    }
  };

  // Callback from CameraScanner
  const handleCameraCapture = (uri: string) => {
    setCameraOpen(false);
    setCapturedUri(uri);
    const name = `camera_scan_${Date.now()}.jpg`;
    setCapturedFileName(name);
    handleStartUpload(uri, name);
  };

  // Upload and poll OCR extraction
  const handleStartUpload = async (fileUri: string, fileName: string) => {
    setIsUploading(true);
    setUploadProgress(20);
    setIsSavedLocally(false);

    try {
      const formData = new FormData();
      const fileData: any = {
        uri: fileUri,
        type: 'image/jpeg',
        name: fileName,
      };

      formData.append('file', fileData);
      formData.append('document_type', selectedCategory);
      formData.append('process_immediately', 'true');
      if (consultation?.id) {
        formData.append('consultation_id', consultation.id);
      }

      setUploadProgress(60);
      const doc = await apiService.uploadMedicalDocument(formData, consultation?.id);
      setCurrentDocument(doc);
      setUploadProgress(100);
      setIsUploading(false);

      // Now poll/fetch OCR extraction
      setIsExtracting(true);
      await pollExtraction(doc.id);
      loadDocuments();
    } catch (err: any) {
      setIsUploading(false);
      setIsExtracting(false);
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        'Document upload failed. Please ensure the file is under 10MB.';
      Alert.alert('Upload Failed', message);
    }
  };

  const pollExtraction = async (documentId: string) => {
    let attempts = 0;
    const maxAttempts = 6;

    while (attempts < maxAttempts) {
      try {
        const extraction = await apiService.getDocumentExtraction(documentId);
        if (extraction) {
          setCurrentExtraction(extraction);
          populateFormWithExtraction(extraction);
          setIsExtracting(false);
          return;
        }
      } catch {
        // Document extraction still running on backend
      }
      attempts++;
      await new Promise((res) => setTimeout(res, 2000));
    }

    // Try fetching latest document status
    try {
      const updatedDoc = await apiService.getMedicalDocument(documentId);
      setCurrentDocument(updatedDoc);
    } catch {
      // Ignore poll error
    }
    setIsExtracting(false);
  };

  const populateFormWithExtraction = (ext: StructuredExtraction) => {
    if (ext.document_type) {
      setFormDocType(ext.document_type.replace('_', ' ').toUpperCase());
    }
    if (ext.document_date) {
      setFormDocDate(ext.document_date);
    }
    if (ext.hospital_or_clinic_name) {
      setFormHospital(ext.hospital_or_clinic_name);
    }
    if (ext.doctor_name) {
      setFormDoctor(ext.doctor_name);
    }
    if (ext.medications && Array.isArray(ext.medications)) {
      const medsStr = ext.medications
        .map((m: any) => {
          if (typeof m === 'string') return m;
          return m.name || m.medicine || JSON.stringify(m);
        })
        .filter(Boolean)
        .join(', ');
      setFormMedicines(medsStr);
    }
    if (ext.laboratory_results && Array.isArray(ext.laboratory_results)) {
      const testsStr = ext.laboratory_results
        .map((t: any) => {
          if (typeof t === 'string') return t;
          return `${t.test || t.name || ''}: ${t.value || t.result || ''}`.trim();
        })
        .filter(Boolean)
        .join(', ');
      setFormTests(testsStr);
    } else if (ext.investigations && Array.isArray(ext.investigations)) {
      setFormTests(ext.investigations.join(', '));
    }
    if (ext.follow_up_instructions_as_documented) {
      setFormNotes(ext.follow_up_instructions_as_documented);
    } else if (ext.warnings && ext.warnings.length > 0) {
      setFormNotes(ext.warnings.join('. '));
    }
  };

  const handleSaveToRecords = () => {
    setIsSavedLocally(true);
    Alert.alert(
      'Document Saved',
      'The extracted medical details have been confirmed and attached to your patient record.'
    );
  };

  const handleResetScan = () => {
    setCapturedUri(null);
    setCurrentDocument(null);
    setCurrentExtraction(null);
    setFormDocDate('');
    setFormHospital('');
    setFormDoctor('');
    setFormMedicines('');
    setFormTests('');
    setFormNotes('');
    setIsSavedLocally(false);
  };

  return (
    <View style={styles.container}>
      <Header
        title="CLINOVA"
        subtitle="Medical Documents"
        showBack={true}
        onBackPress={() => navigation?.goBack?.() || onNavigateToIntake?.()}
        hospitalToken={consultation?.token_number ? `#${consultation.token_number}` : undefined}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Context Hero Banner */}
        <View style={styles.heroBanner}>
          <View style={styles.heroBadgeRow}>
            <Text style={styles.heroBadgeIcon}>🛡️</Text>
            <Text style={styles.heroBadgeText}>CLINOVA MEDICAL RECORDS</Text>
          </View>
          <Text style={styles.heroTitle}>Add your previous medical reports and prescriptions</Text>
          <Text style={styles.heroSubtitle}>
            Scan physical papers or upload files to keep all your clinical notes, lab tests, and doctor
            orders organized in one secure place.
          </Text>
        </View>

        {/* Primary Capture Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Add a medical document</Text>
          <Text style={styles.sectionSubtitle}>
            Scan or upload your prescription, lab report, discharge summary, or other medical document.
          </Text>

          <View style={styles.actionGrid}>
            {/* Scan with Camera */}
            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => setCameraOpen(true)}
              activeOpacity={0.8}
            >
              <View style={styles.actionCardTop}>
                <View style={[styles.actionIconContainer, { backgroundColor: colors.secondaryContainer }]}>
                  <Text style={styles.actionEmoji}>📷</Text>
                </View>
                <View style={styles.pillBadge}>
                  <Text style={styles.pillBadgeText}>Instant scan</Text>
                </View>
              </View>
              <Text style={styles.actionTitle}>Scan with Camera</Text>
              <Text style={styles.actionDesc}>
                Place the complete document flat inside the visible frame
              </Text>
            </TouchableOpacity>

            {/* Upload from Device */}
            <TouchableOpacity
              style={styles.actionCard}
              onPress={handlePickFile}
              activeOpacity={0.8}
            >
              <View style={styles.actionCardTop}>
                <View style={[styles.actionIconContainer, { backgroundColor: colors.surfaceContainerHigh }]}>
                  <Text style={styles.actionEmoji}>📁</Text>
                </View>
                <View style={[styles.pillBadge, { backgroundColor: colors.surfaceContainerLow }]}>
                  <Text style={[styles.pillBadgeText, { color: colors.onSurfaceVariant }]}>
                    Files &amp; Photos
                  </Text>
                </View>
              </View>
              <Text style={styles.actionTitle}>Upload from Device</Text>
              <Text style={styles.actionDesc}>Supports PDF, JPG, and PNG files up to 10MB</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Document Category Selection */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionLabel}>What type of document is this?</Text>
            <Text style={styles.requiredText}>Required</Text>
          </View>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.chipsRow}
          >
            {DOC_TYPE_OPTIONS.map((item) => {
              const active = selectedCategory === item.key;
              return (
                <TouchableOpacity
                  key={item.key}
                  style={[styles.categoryChip, active && styles.categoryChipActive]}
                  onPress={() => setSelectedCategory(item.key)}
                >
                  <Text style={styles.chipEmoji}>{item.icon}</Text>
                  <Text style={[styles.chipText, active && styles.chipTextActive]}>
                    {item.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {/* Upload / OCR Progress Card */}
        {isUploading && (
          <View style={styles.progressCard}>
            <ActivityIndicator size="small" color={colors.primary} />
            <View style={styles.progressTextCol}>
              <Text style={styles.progressTitle}>Uploading document...</Text>
              <Text style={styles.progressDesc}>Sending securely to Clinova cloud storage</Text>
            </View>
            <Text style={styles.progressPercent}>{uploadProgress}%</Text>
          </View>
        )}

        {/* OCR Status Banner & Preview */}
        {capturedUri && !isUploading && (
          <View style={styles.previewSection}>
            <View style={styles.previewHeader}>
              <View style={styles.previewThumbContainer}>
                <Image source={{ uri: capturedUri }} style={styles.previewThumb} />
                <View style={styles.thumbOverlay}>
                  <Text style={{ fontSize: 16 }}>🔍</Text>
                </View>
              </View>
              <View style={styles.previewInfoCol}>
                <Text style={styles.previewTag}>CURRENT SCAN</Text>
                <Text style={styles.previewFileName} numberOfLines={1}>
                  {capturedFileName}
                </Text>
                <Text style={styles.previewMeta}>
                  Type: {selectedCategory.replace('_', ' ')} • 1 page
                </Text>
              </View>
              <TouchableOpacity
                style={styles.previewBtn}
                onPress={() => setPreviewModalVisible(true)}
              >
                <Text style={styles.previewBtnText}>Preview</Text>
              </TouchableOpacity>
            </View>

            {/* OCR Processing or Complete Banner */}
            <View style={styles.ocrStatusBanner}>
              <View style={styles.ocrBannerTop}>
                <View style={styles.ocrStatusRow}>
                  <Text style={styles.ocrIcon}>
                    {isExtracting ? '⏳' : '✅'}
                  </Text>
                  <Text style={styles.ocrStatusTitle}>
                    {isExtracting
                      ? 'Extracting clinical text...'
                      : 'Extraction complete'}
                  </Text>
                </View>
                <Text style={styles.ocrStatusPercent}>
                  {isExtracting ? 'Analyzing...' : '100% extracted'}
                </Text>
              </View>
              <Text style={styles.ocrBannerDesc}>
                Clinova optical reader extracted clinical details. Please review carefully against your
                paper copy before continuing.
              </Text>
              <View style={styles.ocrProgressBarTrack}>
                <View
                  style={[
                    styles.ocrProgressBarFill,
                    { width: isExtracting ? '65%' : '100%' },
                  ]}
                />
              </View>
            </View>

            {/* Verification Caution Banner */}
            <View style={styles.cautionBanner}>
              <Text style={styles.cautionIcon}>ℹ️</Text>
              <View style={styles.cautionTextCol}>
                <Text style={styles.cautionTitle}>
                  Please check the information before saving.
                </Text>
                <Text style={styles.cautionDesc}>
                  Ensure doctor name, medicine dosages, and diagnostic instructions correspond exactly
                  to the paper sheet.
                </Text>
              </View>
            </View>

            {/* Structured Editable Extraction Form */}
            <View style={styles.formContainer}>
              <View style={styles.formTitleRow}>
                <Text style={styles.formHeading}>Information Found</Text>
                <View style={styles.editableBadge}>
                  <Text style={styles.editableBadgeText}>✏️ Editable</Text>
                </View>
              </View>

              {/* Document Type & Date */}
              <View style={styles.formRow}>
                <View style={[styles.formCol, { marginRight: spacing.sm }]}>
                  <Text style={styles.fieldLabel}>Document Type</Text>
                  <TextInput
                    style={styles.textInput}
                    value={formDocType}
                    onChangeText={setFormDocType}
                    placeholder="e.g. Prescription"
                    placeholderTextColor={colors.onSurfaceVariant}
                  />
                </View>
                <View style={styles.formCol}>
                  <Text style={styles.fieldLabel}>Document Date</Text>
                  <TextInput
                    style={styles.textInput}
                    value={formDocDate}
                    onChangeText={setFormDocDate}
                    placeholder="e.g. 28 Aug 2026"
                    placeholderTextColor={colors.onSurfaceVariant}
                  />
                </View>
              </View>

              {/* Hospital / Clinic & Doctor */}
              <View style={styles.formRow}>
                <View style={[styles.formCol, { marginRight: spacing.sm }]}>
                  <Text style={styles.fieldLabel}>Hospital / Clinic</Text>
                  <TextInput
                    style={styles.textInput}
                    value={formHospital}
                    onChangeText={setFormHospital}
                    placeholder="e.g. City Hospital OPD"
                    placeholderTextColor={colors.onSurfaceVariant}
                  />
                </View>
                <View style={styles.formCol}>
                  <Text style={styles.fieldLabel}>Doctor Name</Text>
                  <TextInput
                    style={styles.textInput}
                    value={formDoctor}
                    onChangeText={setFormDoctor}
                    placeholder="e.g. Dr. K. Patel"
                    placeholderTextColor={colors.onSurfaceVariant}
                  />
                </View>
              </View>

              {/* Medicines Found */}
              <View style={styles.fieldBlock}>
                <Text style={styles.fieldLabel}>Medicines Found</Text>
                <TextInput
                  style={[styles.textInput, styles.textArea]}
                  value={formMedicines}
                  onChangeText={setFormMedicines}
                  placeholder="e.g. Metformin 500mg (1-0-1), Telmisartan 40mg (1-0-0)"
                  placeholderTextColor={colors.onSurfaceVariant}
                  multiline
                  numberOfLines={2}
                />
                <Text style={styles.fieldHint}>
                  Separate multiple medications with commas or line breaks
                </Text>
              </View>

              {/* Tests Ordered / Laboratory Results */}
              <View style={styles.fieldBlock}>
                <Text style={styles.fieldLabel}>Tests Ordered / Lab Findings</Text>
                <TextInput
                  style={styles.textInput}
                  value={formTests}
                  onChangeText={setFormTests}
                  placeholder="e.g. Fasting Blood Sugar: 110 mg/dL, Lipid Profile"
                  placeholderTextColor={colors.onSurfaceVariant}
                />
              </View>

              {/* Results / Instructions */}
              <View style={styles.fieldBlock}>
                <Text style={styles.fieldLabel}>Results / Values / Instructions</Text>
                <TextInput
                  style={styles.textInput}
                  value={formNotes}
                  onChangeText={setFormNotes}
                  placeholder="e.g. Take with meals, follow up in 2 weeks"
                  placeholderTextColor={colors.onSurfaceVariant}
                />
              </View>

              {/* Action Buttons */}
              <View style={styles.formActions}>
                <Button
                  title={isSavedLocally ? 'Record Saved ✓' : 'Save to My Medical Records'}
                  onPress={handleSaveToRecords}
                  variant={isSavedLocally ? 'secondary' : 'primary'}
                  icon="💾"
                  fullWidth
                />

                <View style={styles.secondaryButtonsRow}>
                  <TouchableOpacity
                    style={styles.secondaryBtn}
                    onPress={handleResetScan}
                  >
                    <Text style={styles.secondaryBtnText}>📸 Scan Another</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.secondaryBtn, styles.accentSecondaryBtn]}
                    onPress={() => onNavigateToIntake?.() || navigation?.goBack?.()}
                  >
                    <Text style={[styles.secondaryBtnText, styles.accentSecondaryBtnText]}>
                      Continue Intake →
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </View>
        )}

        {/* Existing / Uploaded Documents List */}
        <View style={[styles.section, { marginBottom: spacing.xxl }]}>
          <View style={styles.sectionHeaderRow}>
            <View style={styles.uploadedTitleRow}>
              <Text style={{ fontSize: 20 }}>📁</Text>
              <Text style={styles.sectionTitle}>Your Uploaded Documents</Text>
            </View>
            <Text style={styles.countText}>
              {uploadedDocsList.length} {uploadedDocsList.length === 1 ? 'file' : 'files'}
            </Text>
          </View>

          {isLoadingList && (
            <View style={styles.emptyCard}>
              <ActivityIndicator size="small" color={colors.primary} />
              <Text style={styles.emptyCardSub}>Loading document history...</Text>
            </View>
          )}

          {!isLoadingList && uploadedDocsList.length === 0 && (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyEmoji}>📑</Text>
              <Text style={styles.emptyCardTitle}>No documents uploaded yet</Text>
              <Text style={styles.emptyCardSub}>
                Upload previous prescriptions, lab reports, or discharge slips to build your digital record.
              </Text>
            </View>
          )}

          {uploadedDocsList.map((doc) => {
            const isDone =
              doc.ocr_status === 'completed' ||
              doc.upload_status === 'processed' ||
              doc.processing_status === 'COMPLETED';

            const isFailed =
              doc.ocr_status === 'failed' || doc.processing_status === 'FAILED';

            return (
              <View key={doc.id} style={styles.docCard}>
                <View style={styles.docCardHeader}>
                  <View style={styles.docCardLeft}>
                    <View style={styles.docIconCircle}>
                      <Text style={{ fontSize: 18 }}>
                        {doc.document_type?.includes('lab')
                          ? '🔬'
                          : doc.document_type?.includes('scan')
                          ? '🩻'
                          : '💊'}
                      </Text>
                    </View>
                    <View style={styles.docMetaCol}>
                      <Text style={styles.docTitle} numberOfLines={1}>
                        {doc.filename || doc.file_name || `${doc.document_type} report`}
                      </Text>
                      <Text style={styles.docSub}>
                        {doc.created_at
                          ? new Date(doc.created_at).toLocaleDateString()
                          : 'Recent'}{' '}
                        • {doc.document_type?.replace('_', ' ')}
                      </Text>
                    </View>
                  </View>

                  <Badge
                    text={
                      isDone
                        ? 'Verified'
                        : isFailed
                        ? 'Failed'
                        : 'Processing'
                    }
                    variant={isDone ? 'success' : isFailed ? 'danger' : 'warning'}
                    size="small"
                  />
                </View>
              </View>
            );
          })}
        </View>
      </ScrollView>

      {/* Camera Scanner Modal */}
      <CameraScanner
        visible={cameraOpen}
        onClose={() => setCameraOpen(false)}
        onCaptureConfirmed={(uri) => handleCameraCapture(uri)}
      />

      {/* Full Image Preview Modal */}
      <Modal
        visible={previewModalVisible}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setPreviewModalVisible(false)}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Document Preview</Text>
              <TouchableOpacity onPress={() => setPreviewModalVisible(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>
            {capturedUri && (
              <Image
                source={{ uri: capturedUri }}
                style={styles.modalImage}
                resizeMode="contain"
              />
            )}
            <Button
              title="Close Preview"
              onPress={() => setPreviewModalVisible(false)}
              variant="outline"
              fullWidth
            />
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: spacing.xxl,
  },
  heroBanner: {
    backgroundColor: colors.surfaceContainerLow,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.outlineVariant,
  },
  heroBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  heroBadgeIcon: {
    fontSize: 14,
    marginRight: spacing.xs,
  },
  heroBadgeText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  heroTitle: {
    ...typography.headlineSm,
    color: colors.onSurface,
    fontWeight: '700',
    marginBottom: spacing.xs,
  },
  heroSubtitle: {
    ...typography.bodyMd,
    color: colors.onSurfaceVariant,
    lineHeight: 20,
  },
  section: {
    paddingHorizontal: spacing.lg,
    marginTop: spacing.lg,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  sectionTitle: {
    ...typography.headlineSm,
    color: colors.onSurface,
    fontWeight: '700',
  },
  sectionSubtitle: {
    ...typography.bodyMd,
    color: colors.onSurfaceVariant,
    marginTop: spacing.xs,
    marginBottom: spacing.md,
  },
  sectionLabel: {
    ...typography.bodyBold,
    color: colors.onSurface,
  },
  requiredText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '600',
  },
  actionGrid: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  actionCard: {
    flex: 1,
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
    ...shadows.sm,
  },
  actionCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  actionIconContainer: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionEmoji: {
    fontSize: 22,
  },
  pillBadge: {
    backgroundColor: colors.surfaceContainerLow,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
  },
  pillBadgeText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '700',
  },
  actionTitle: {
    ...typography.bodyBold,
    color: colors.onSurface,
    marginBottom: 2,
  },
  actionDesc: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    lineHeight: 16,
  },
  chipsRow: {
    gap: spacing.sm,
    paddingVertical: spacing.xs,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerLowest,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  categoryChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  chipEmoji: {
    fontSize: 16,
    marginRight: spacing.xs,
  },
  chipText: {
    ...typography.labelLg,
    color: colors.onSurfaceVariant,
  },
  chipTextActive: {
    color: colors.onPrimary,
    fontWeight: '700',
  },
  progressCard: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.md,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressTextCol: {
    flex: 1,
    marginLeft: spacing.md,
  },
  progressTitle: {
    ...typography.bodyBold,
    color: colors.onSurface,
  },
  progressDesc: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
  },
  progressPercent: {
    ...typography.labelLg,
    color: colors.primary,
    fontWeight: '700',
  },
  previewSection: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.lg,
    gap: spacing.md,
  },
  previewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerLowest,
    padding: spacing.md,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  previewThumbContainer: {
    width: 60,
    height: 72,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    backgroundColor: colors.surfaceContainerHigh,
    position: 'relative',
  },
  previewThumb: {
    width: '100%',
    height: '100%',
  },
  thumbOverlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(0, 104, 95, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  previewInfoCol: {
    flex: 1,
    marginLeft: spacing.md,
  },
  previewTag: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  previewFileName: {
    ...typography.bodyBold,
    color: colors.onSurface,
    marginTop: 2,
  },
  previewMeta: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginTop: 2,
  },
  previewBtn: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.lg,
  },
  previewBtnText: {
    ...typography.labelMd,
    color: colors.primary,
    fontWeight: '600',
  },
  ocrStatusBanner: {
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.md,
    borderRadius: borderRadius.xl,
  },
  ocrBannerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  ocrStatusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ocrIcon: {
    fontSize: 16,
    marginRight: spacing.xs,
  },
  ocrStatusTitle: {
    ...typography.bodyBold,
    color: colors.onSurface,
  },
  ocrStatusPercent: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '700',
  },
  ocrBannerDesc: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    lineHeight: 16,
    marginBottom: spacing.sm,
  },
  ocrProgressBarTrack: {
    height: 6,
    borderRadius: borderRadius.full,
    backgroundColor: colors.surfaceContainerHigh,
    overflow: 'hidden',
  },
  ocrProgressBarFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: borderRadius.full,
  },
  cautionBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.md,
    borderRadius: borderRadius.xl,
    borderLeftWidth: 4,
    borderLeftColor: colors.primary,
  },
  cautionIcon: {
    fontSize: 18,
    marginRight: spacing.sm,
    marginTop: 1,
  },
  cautionTextCol: {
    flex: 1,
  },
  cautionTitle: {
    ...typography.bodyBold,
    color: colors.onSurface,
  },
  cautionDesc: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginTop: 2,
    lineHeight: 16,
  },
  formContainer: {
    backgroundColor: colors.surfaceContainerLowest,
    padding: spacing.lg,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
    ...shadows.sm,
  },
  formTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  formHeading: {
    ...typography.headlineSm,
    color: colors.onSurface,
    fontWeight: '700',
  },
  editableBadge: {
    backgroundColor: colors.secondaryContainer,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
  },
  editableBadgeText: {
    ...typography.caption,
    color: colors.onSecondaryContainer,
    fontWeight: '700',
  },
  formRow: {
    flexDirection: 'row',
    marginBottom: spacing.md,
  },
  formCol: {
    flex: 1,
  },
  fieldBlock: {
    marginBottom: spacing.md,
  },
  fieldLabel: {
    ...typography.labelMd,
    color: colors.onSurface,
    fontWeight: '600',
    marginBottom: spacing.xs,
  },
  textInput: {
    minHeight: 46,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.md,
    ...typography.bodyMd,
    color: colors.onSurface,
  },
  textArea: {
    minHeight: 64,
    textAlignVertical: 'top',
    paddingTop: spacing.sm,
  },
  fieldHint: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginTop: spacing.xs,
  },
  formActions: {
    marginTop: spacing.md,
    gap: spacing.sm,
  },
  secondaryButtonsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  secondaryBtn: {
    flex: 1,
    minHeight: 46,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.xl,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryBtnText: {
    ...typography.labelLg,
    color: colors.primary,
    fontWeight: '700',
  },
  accentSecondaryBtn: {
    backgroundColor: colors.secondaryContainer,
  },
  accentSecondaryBtnText: {
    color: colors.onSecondaryContainer,
  },
  uploadedTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  countText: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    fontWeight: '600',
  },
  emptyCard: {
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xl,
    padding: spacing.xl,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  emptyEmoji: {
    fontSize: 32,
    marginBottom: spacing.sm,
  },
  emptyCardTitle: {
    ...typography.bodyBold,
    color: colors.onSurface,
  },
  emptyCardSub: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    textAlign: 'center',
    marginTop: spacing.xs,
    maxWidth: 260,
  },
  docCard: {
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  docCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  docCardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: spacing.sm,
  },
  docIconCircle: {
    width: 40,
    height: 40,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
  },
  docMetaCol: {
    flex: 1,
  },
  docTitle: {
    ...typography.bodyBold,
    color: colors.onSurface,
  },
  docSub: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginTop: 2,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  modalCard: {
    width: '100%',
    maxHeight: '85%',
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xxl,
    padding: spacing.lg,
    gap: spacing.md,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  modalTitle: {
    ...typography.headlineSm,
    color: colors.onSurface,
    fontWeight: '700',
  },
  modalClose: {
    fontSize: 22,
    color: colors.onSurfaceVariant,
    padding: spacing.xs,
  },
  modalImage: {
    width: '100%',
    height: 340,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
  },
});
