import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp, ScreenRouteProp } from '../../navigation/types';
import { documentApi } from '../../api';
import { MedicalDocument, StructuredExtraction } from '../../types';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Button from '../../components/Button';
import Badge from '../../components/Badge';

export const DocumentExtractionScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'DocumentExtraction'>>();
  const route = useRoute<ScreenRouteProp<'DocumentExtraction'>>();
  const { documentId } = route.params;

  const [document, setDocument] = useState<MedicalDocument | null>(null);
  const [extraction, setExtraction] = useState<StructuredExtraction | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [docRes, extRes] = await Promise.allSettled([
        documentApi.getDocument(documentId),
        documentApi.getExtraction(documentId),
      ]);

      if (docRes.status === 'fulfilled') {
        setDocument(docRes.value);
      }
      if (extRes.status === 'fulfilled') {
        setExtraction(extRes.value);
      }
    } catch (err: any) {
      setError('Unable to load document extraction details.');
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRetryProcessing = async () => {
    try {
      setProcessing(true);
      setError(null);
      await documentApi.processDocument(documentId);
      await loadData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Processing failed. Please retry.');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <View style={styles.container}>
      <Header title="Document Extraction" onBack={() => navigation.goBack()} />

      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Retrieving extracted clinical data...</Text>
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorBoxText}>{error}</Text>
            </View>
          )}

          {/* Metadata Card */}
          <Card elevated style={styles.metaCard}>
            <View style={styles.metaRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.docTitle}>
                  {document?.filename || document?.file_name || 'Medical Document'}
                </Text>
                <Text style={styles.docType}>
                  Type: {document?.document_type.replace('_', ' ').toUpperCase()}
                </Text>
                <Text style={styles.docDate}>
                  Uploaded: {document?.created_at ? new Date(document.created_at).toLocaleDateString() : 'N/A'}
                </Text>
              </View>
              <Badge
                label={document?.ocr_status === 'completed' ? 'Processed' : 'In Progress'}
                variant={document?.ocr_status === 'completed' ? 'verified' : 'yellow'}
              />
            </View>

            {document?.ocr_status !== 'completed' && (
              <Button
                title="Run / Retry OCR Extraction"
                onPress={handleRetryProcessing}
                loading={processing}
                variant="secondary"
                style={{ marginTop: spacing.md }}
              />
            )}
          </Card>

          {/* Structured Clinical Extraction Results */}
          {extraction ? (
            <>
              {/* Doctor / Facility */}
              {(extraction.doctor_name || extraction.hospital_or_clinic_name) && (
                <Card style={styles.sectionCard}>
                  <Text style={styles.sectionHeader}>Facility & Clinician</Text>
                  {extraction.hospital_or_clinic_name && (
                    <Text style={styles.itemText}>
                      <Text style={styles.bold}>Facility: </Text>
                      {extraction.hospital_or_clinic_name}
                    </Text>
                  )}
                  {extraction.doctor_name && (
                    <Text style={styles.itemText}>
                      <Text style={styles.bold}>Doctor: </Text>
                      {extraction.doctor_name}
                    </Text>
                  )}
                </Card>
              )}

              {/* Diagnoses */}
              {((extraction.diagnosis && extraction.diagnosis.length > 0) ||
                (extraction.diagnoses_or_conditions_as_documented &&
                  extraction.diagnoses_or_conditions_as_documented.length > 0)) && (
                <Card style={styles.sectionCard}>
                  <Text style={styles.sectionHeader}>Documented Diagnoses</Text>
                  {(extraction.diagnosis || extraction.diagnoses_or_conditions_as_documented || []).map(
                    (d, idx) => (
                      <Text key={idx} style={styles.bulletItem}>
                        • {d}
                      </Text>
                    )
                  )}
                </Card>
              )}

              {/* Documented Symptoms */}
              {extraction.symptoms_as_documented && extraction.symptoms_as_documented.length > 0 && (
                <Card style={styles.sectionCard}>
                  <Text style={styles.sectionHeader}>Documented Symptoms</Text>
                  {extraction.symptoms_as_documented.map((s, idx) => (
                    <Text key={idx} style={styles.bulletItem}>
                      • {s}
                    </Text>
                  ))}
                </Card>
              )}

              {/* Medications */}
              {extraction.medications && extraction.medications.length > 0 && (
                <Card style={styles.sectionCard}>
                  <Text style={styles.sectionHeader}>Medications Found</Text>
                  {extraction.medications.map((m, idx) => (
                    <View key={idx} style={styles.medicationRow}>
                      <Ionicons name="medical" size={16} color={colors.primary} />
                      <View style={{ marginLeft: spacing.xs + 2 }}>
                        <Text style={styles.medName}>{m.name}</Text>
                        <Text style={styles.medDetails}>
                          {[m.dosage, m.frequency, m.duration].filter(Boolean).join(' • ')}
                        </Text>
                      </View>
                    </View>
                  ))}
                </Card>
              )}

              {/* Laboratory Results */}
              {extraction.laboratory_results && extraction.laboratory_results.length > 0 && (
                <Card style={styles.sectionCard}>
                  <Text style={styles.sectionHeader}>Laboratory Findings</Text>
                  {extraction.laboratory_results.map((lab, idx) => (
                    <View key={idx} style={styles.labRow}>
                      <Text style={styles.labTestName}>{lab.test_name}</Text>
                      <Text style={styles.labValue}>
                        {lab.result_value} {lab.unit || ''}
                      </Text>
                    </View>
                  ))}
                </Card>
              )}

              {/* Warnings / Red Flags */}
              {extraction.warnings && extraction.warnings.length > 0 && (
                <Card style={[styles.sectionCard, styles.warningCard]}>
                  <Text style={[styles.sectionHeader, { color: colors.triageRed }]}>
                    Document Clinical Warnings
                  </Text>
                  {extraction.warnings.map((w, idx) => (
                    <Text key={idx} style={[styles.bulletItem, { color: '#991B1B' }]}>
                      ⚠️ {w}
                    </Text>
                  ))}
                </Card>
              )}

              {/* Raw OCR Text Preview */}
              {extraction.cleaned_text && (
                <Card style={styles.sectionCard}>
                  <Text style={styles.sectionHeader}>Raw OCR Extracted Text</Text>
                  <Text style={styles.rawOcrText}>{extraction.cleaned_text}</Text>
                </Card>
              )}
            </>
          ) : (
            <Card style={styles.emptyExtractionCard}>
              <Ionicons name="time-outline" size={36} color={colors.textMuted} />
              <Text style={styles.emptyTitle}>Extraction In Progress or Pending</Text>
              <Text style={styles.emptySubtitle}>
                The AI OCR engine processes document text asynchronously. Pull to refresh or tap
                below to re-trigger extraction.
              </Text>
              <Button
                title="Trigger OCR Processing"
                onPress={handleRetryProcessing}
                loading={processing}
                style={{ marginTop: spacing.md }}
              />
            </Card>
          )}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  loadingText: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
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
  },
  metaCard: {
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  docTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.onSurface,
  },
  docType: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
    marginTop: 2,
  },
  docDate: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  sectionCard: {
    marginBottom: spacing.sm,
    padding: spacing.md,
  },
  sectionHeader: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  itemText: {
    fontSize: 13,
    color: colors.onSurface,
    marginBottom: 2,
  },
  bold: {
    fontWeight: '700',
  },
  bulletItem: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
    lineHeight: 18,
    marginBottom: 2,
  },
  medicationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
    paddingVertical: 2,
  },
  medName: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.onSurface,
  },
  medDetails: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  labRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  labTestName: {
    fontSize: 13,
    color: colors.onSurface,
  },
  labValue: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.primary,
  },
  warningCard: {
    backgroundColor: colors.triageRedBg,
    borderColor: colors.triageRedBorder,
  },
  rawOcrText: {
    fontSize: 12,
    color: colors.onSurfaceVariant,
    lineHeight: 18,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.sm,
    borderRadius: borderRadius.sm,
  },
  emptyExtractionCard: {
    alignItems: 'center',
    padding: spacing.xl,
    marginTop: spacing.md,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.onSurface,
    marginTop: spacing.sm,
  },
  emptySubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 4,
    lineHeight: 18,
  },
});

export default DocumentExtractionScreen;
