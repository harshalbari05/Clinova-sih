import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp, ScreenRouteProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import { consultationApi } from '../../api';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Button from '../../components/Button';
import StepIndicator from '../../components/StepIndicator';

export const ConsentScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'Consent'>>();
  const route = useRoute<ScreenRouteProp<'Consent'>>();
  const { hospitalId } = route.params;

  const { selectedHospital, setActiveConsultation, setConsentGiven } = usePatient();

  const [hasAgreed, setHasAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGrantConsent = async () => {
    if (!hasAgreed) {
      setError('You must explicitly check the informed consent box to proceed.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // 1. Create the consultation session
      const consultation = await consultationApi.createConsultation({
        hospital_id: hospitalId,
        chief_complaint: 'Clinical intake consultation',
      });

      // 2. Record explicit patient consent in backend
      await consultationApi.recordConsent(consultation.id, {
        consent_given: true,
        consent_type: 'clinical_intake',
      });

      await setActiveConsultation(consultation);
      await setConsentGiven(true);

      // 3. Move to language selection
      navigation.navigate('LanguageSelect', { consultationId: consultation.id });
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to record consent. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Header title="Patient Informed Consent" onBack={() => navigation.goBack()} />
      <StepIndicator currentStep={2} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Card elevated style={styles.card}>
          <View style={styles.headerRow}>
            <Ionicons name="shield-checkmark-outline" size={28} color={colors.primary} />
            <Text style={styles.cardTitle}>Informed Consent for Clinical Intake</Text>
          </View>

          <Text style={styles.hospitalNotice}>
            Facility:{' '}
            <Text style={{ fontWeight: '700' }}>
              {selectedHospital?.name || 'Selected Hospital'}
            </Text>
          </Text>

          {error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorBoxText}>{error}</Text>
            </View>
          )}

          <View style={styles.section}>
            <Text style={styles.sectionHeading}>1. Purpose of Clinical Intake</Text>
            <Text style={styles.sectionText}>
              Clinova gathers your medical symptoms, relevant health history, and uploaded
              documents ahead of your consultation to assist your physician in preparing a high-quality
              clinical overview.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionHeading}>2. Information Collected</Text>
            <Text style={styles.sectionText}>
              • Chief complaints and duration of symptoms.{'\n'}
              • Medical history, medications, allergies, and prior procedures.{'\n'}
              • Uploaded documents (prescriptions, laboratory reports, discharge summaries).{'\n'}
              • Demographic data and contact numbers.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionHeading}>3. AI Assisting & Non-Diagnostic Role</Text>
            <Text style={styles.sectionText}>
              AI interview and OCR services summarize facts objectively. The AI engine{' '}
              <Text style={{ fontWeight: '700' }}>does NOT</Text> provide medical diagnoses or prescribe
              treatments. All summaries remain drafts until reviewed and approved by a qualified physician.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionHeading}>4. Data Security & Patient Rights</Text>
            <Text style={styles.sectionText}>
              Your information is encrypted, isolated to your affiliated hospital healthcare team, and never
              sold or shared for advertising. You may decline or revoke consent at any time.
            </Text>
          </View>

          {/* Explicit Consent Checkbox */}
          <TouchableOpacity
            style={styles.checkboxRow}
            activeOpacity={0.8}
            onPress={() => {
              setHasAgreed(!hasAgreed);
              setError(null);
            }}
          >
            <View style={[styles.checkbox, hasAgreed && styles.checkboxChecked]}>
              {hasAgreed && <Ionicons name="checkmark" size={16} color={colors.onPrimary} />}
            </View>
            <Text style={styles.checkboxLabel}>
              I have read, understood, and explicitly grant consent for pre-consultation clinical
              intake and AI-assisted data processing.
            </Text>
          </TouchableOpacity>

          <Button
            title="Grant Consent & Continue"
            onPress={handleGrantConsent}
            loading={loading}
            disabled={!hasAgreed}
            style={styles.actionBtn}
          />

          <Button
            title="Cancel & Exit"
            variant="outline"
            onPress={() => navigation.goBack()}
            style={{ marginTop: spacing.sm }}
          />
        </Card>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
  card: {
    padding: spacing.lg,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.onSurface,
    marginLeft: spacing.xs + 2,
    flex: 1,
  },
  hospitalNotice: {
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: spacing.md,
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
  section: {
    marginBottom: spacing.md,
  },
  sectionHeading: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary,
    marginBottom: 2,
  },
  sectionText: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
    lineHeight: 18,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginVertical: spacing.md,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
    marginTop: 2,
    backgroundColor: colors.surfaceContainerLowest,
  },
  checkboxChecked: {
    backgroundColor: colors.primary,
  },
  checkboxLabel: {
    fontSize: 13,
    color: colors.onSurface,
    flex: 1,
    lineHeight: 18,
    fontWeight: '500',
  },
  actionBtn: {
    marginTop: spacing.sm,
  },
});

export default ConsentScreen;
