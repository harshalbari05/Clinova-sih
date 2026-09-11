/**
 * ConsentScreen
 *
 * Shown once after first login, before the patient reaches the dashboard.
 * Does NOT require hospital selection — consent is a patient-level agreement.
 * Hospital assignment happens later at the hospital reception.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { usePatient } from '../../context/PatientContext';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Card from '../../components/Card';
import Button from '../../components/Button';

export const ConsentScreen: React.FC = () => {
  const { setConsentGiven, patient, logout } = usePatient();

  const [hasAgreed, setHasAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGrantConsent = async () => {
    if (!hasAgreed) {
      setError('कृपया सहमति बॉक्स चेक करें / Please check the consent box to continue.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Record consent in SecureStore — consultation creation happens later
      // when patient manually starts "Talk to Clinova" from the dashboard.
      await setConsentGiven(true);

      // Navigation is handled automatically by RootNavigator:
      // consentGiven = true → renders the full authenticated stack (Home).
    } catch (err: any) {
      setError('Unable to record consent. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDecline = async () => {
    // Patient declined — log them out so they can reconsider
    await logout();
  };

  return (
    <View style={styles.container}>
      {/* Header — no back button (consent is a required gate) */}
      <View style={styles.header}>
        <View style={styles.headerBrandRow}>
          <View style={styles.brandBadge}>
            <Text style={styles.brandBadgeText}>+</Text>
          </View>
          <Text style={styles.brandName}>Clinova</Text>
        </View>
        <Text style={styles.headerSubtitle}>
          Welcome, {patient?.full_name || 'Patient'}
        </Text>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Card elevated style={styles.card}>
          <View style={styles.headerRow}>
            <Ionicons name="shield-checkmark-outline" size={30} color={colors.primary} />
            <Text style={styles.cardTitle}>Patient Informed Consent</Text>
          </View>

          {error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorBoxText}>{error}</Text>
            </View>
          )}

          <View style={styles.section}>
            <Text style={styles.sectionHeading}>1. What Clinova Does</Text>
            <Text style={styles.sectionText}>
              Clinova helps you record your health symptoms, medical history, and
              documents so your doctor can prepare better for your visit. The AI
              assistant asks simple questions and creates a health summary.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionHeading}>2. Information Collected</Text>
            <Text style={styles.sectionText}>
              • Your health symptoms and duration{'\n'}
              • Medical history, medicines, allergies{'\n'}
              • Uploaded prescriptions and reports{'\n'}
              • Your name and contact number
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionHeading}>3. AI is Not a Doctor</Text>
            <Text style={styles.sectionText}>
              The Clinova AI does{' '}
              <Text style={{ fontWeight: '700' }}>NOT</Text> diagnose diseases or
              prescribe medicines. It only helps summarise your information for
              your doctor.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionHeading}>4. Your Privacy</Text>
            <Text style={styles.sectionText}>
              Your data is encrypted and only shared with your treating healthcare
              team. It is never sold or used for advertising. You can withdraw
              consent at any time from your profile.
            </Text>
          </View>

          {/* Large consent checkbox — accessible touch target */}
          <TouchableOpacity
            style={styles.checkboxRow}
            activeOpacity={0.8}
            onPress={() => {
              setHasAgreed(!hasAgreed);
              setError(null);
            }}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: hasAgreed }}
            accessibilityLabel="I agree to the Clinova informed consent"
          >
            <View style={[styles.checkbox, hasAgreed && styles.checkboxChecked]}>
              {hasAgreed && <Ionicons name="checkmark" size={20} color={colors.onPrimary} />}
            </View>
            <Text style={styles.checkboxLabel}>
              मैं सहमत हूं / मी सहमत आहे{'\n'}
              <Text style={styles.checkboxLabelEn}>
                I agree to the informed consent for AI-assisted clinical intake.
              </Text>
            </Text>
          </TouchableOpacity>

          <Button
            title="हां, मैं सहमत हूं — Proceed"
            onPress={handleGrantConsent}
            loading={loading}
            disabled={!hasAgreed}
            style={styles.actionBtn}
          />

          <Button
            title="Decline & Sign Out"
            variant="outline"
            onPress={handleDecline}
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
  header: {
    alignItems: 'center',
    paddingTop: spacing.xl + 8,
    paddingBottom: spacing.md,
    paddingHorizontal: spacing.lg,
    backgroundColor: colors.surfaceContainerLowest,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerBrandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  brandBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.xs,
  },
  brandBadgeText: {
    color: colors.onPrimary,
    fontSize: 22,
    fontWeight: '700',
    lineHeight: 26,
  },
  brandName: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.primary,
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
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
    marginBottom: spacing.md,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.onSurface,
    marginLeft: spacing.sm,
    flex: 1,
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
    marginBottom: 4,
  },
  sectionText: {
    fontSize: 14,
    color: colors.onSurfaceVariant,
    lineHeight: 20,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginVertical: spacing.md,
    minHeight: 72,
  },
  checkbox: {
    width: 28,
    height: 28,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
    marginTop: 2,
    backgroundColor: colors.surfaceContainerLowest,
    flexShrink: 0,
  },
  checkboxChecked: {
    backgroundColor: colors.primary,
  },
  checkboxLabel: {
    fontSize: 15,
    color: colors.onSurface,
    flex: 1,
    lineHeight: 22,
    fontWeight: '600',
  },
  checkboxLabelEn: {
    fontSize: 13,
    fontWeight: '400',
    color: colors.textSecondary,
  },
  actionBtn: {
    marginTop: spacing.sm,
    paddingVertical: spacing.md,
  },
});

export default ConsentScreen;
