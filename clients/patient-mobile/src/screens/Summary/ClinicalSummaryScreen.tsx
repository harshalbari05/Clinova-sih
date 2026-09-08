import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp, ScreenRouteProp } from '../../navigation/types';
import { summaryApi } from '../../api';
import { ClinicalSummary } from '../../types';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Button from '../../components/Button';
import StepIndicator from '../../components/StepIndicator';

export const ClinicalSummaryScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'ClinicalSummary'>>();
  const route = useRoute<ScreenRouteProp<'ClinicalSummary'>>();
  const { consultationId } = route.params;

  const [summary, setSummary] = useState<ClinicalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    try {
      setError(null);
      const data = await summaryApi.getSummary(consultationId);
      setSummary(data);
    } catch (err: any) {
      setError('Unable to load clinical summary for this consultation.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [consultationId]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchSummary();
  };

  const handleRegenerateDraft = async () => {
    try {
      setRegenerating(true);
      setError(null);
      const data = await summaryApi.generateSummary(consultationId, true);
      setSummary(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to regenerate draft summary.');
    } finally {
      setRegenerating(false);
    }
  };

  const isConfirmed =
    summary?.verification_status === 'confirmed' ||
    summary?.verification_status === 'reviewed';

  return (
    <View style={styles.container}>
      <Header
        title="Clinical Summary"
        onBack={() => navigation.goBack()}
        rightAction={
          <TouchableOpacity
            onPress={() => navigation.navigate('Home')}
            style={styles.homeBtn}
          >
            <Ionicons name="home-outline" size={20} color={colors.primary} />
          </TouchableOpacity>
        }
      />
      <StepIndicator currentStep={6} />

      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading pre-consultation summary...</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />
          }
        >
          {error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorBoxText}>{error}</Text>
            </View>
          )}

          {/* Status & Review State Banner */}
          <Card elevated style={[styles.statusCard, isConfirmed ? styles.confirmedCard : styles.draftCard]}>
            <View style={styles.statusRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.statusTitle}>
                  {isConfirmed ? 'Physician-Approved Summary' : 'Pre-Consultation AI Draft'}
                </Text>
                <Text style={styles.statusSubtitle}>
                  {isConfirmed
                    ? 'Reviewed and validated by your hospital physician.'
                    : 'Objective draft generated from your intake responses and documents.'}
                </Text>
              </View>
              <Badge
                label={isConfirmed ? 'Confirmed' : 'AI Draft'}
                variant={isConfirmed ? 'verified' : 'yellow'}
              />
            </View>

            {!isConfirmed && (
              <View style={styles.disclaimerNotice}>
                <Ionicons name="alert-circle" size={16} color="#B45309" />
                <Text style={styles.disclaimerText}>
                  This summary is an automated intake draft for physician review. It does NOT
                  constitute a clinical diagnosis or treatment plan.
                </Text>
              </View>
            )}
          </Card>

          {/* Chief Complaint */}
          <Card style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>Reported Chief Complaint</Text>
            <Text style={styles.sectionBody}>
              {summary?.chief_complaint || 'General clinical intake'}
            </Text>
          </Card>

          {/* Clinical Narrative / HPI */}
          <Card style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>History of Present Illness (HPI)</Text>
            <Text style={styles.sectionBody}>
              {summary?.history_of_present_illness ||
                summary?.narrative ||
                summary?.ai_draft_text ||
                summary?.summary_text ||
                'Clinical interview details are being summarized.'}
            </Text>
          </Card>

          {/* Clinician Notes if present */}
          {summary?.clinician_notes ? (
            <Card style={[styles.sectionCard, styles.notesCard]}>
              <Text style={[styles.sectionTitle, { color: colors.primary }]}>
                Physician Clinical Notes
              </Text>
              <Text style={styles.sectionBody}>{summary.clinician_notes}</Text>
            </Card>
          ) : null}

          {/* Regeneration Action */}
          {!isConfirmed && (
            <Button
              title="Regenerate Draft Summary"
              variant="outline"
              onPress={handleRegenerateDraft}
              loading={regenerating}
              style={{ marginTop: spacing.md }}
            />
          )}

          <Button
            title="Return to Home Dashboard"
            onPress={() => navigation.navigate('Home')}
            style={{ marginTop: spacing.md }}
          />
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
  homeBtn: {
    padding: spacing.xs,
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
  statusCard: {
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  draftCard: {
    backgroundColor: '#FFFBEB',
    borderColor: '#FDE68A',
  },
  confirmedCard: {
    backgroundColor: '#F0FDF4',
    borderColor: '#86EFAC',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  statusTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.onSurface,
  },
  statusSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
    marginRight: spacing.sm,
    lineHeight: 16,
  },
  disclaimerNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FEF3C7',
    padding: spacing.sm,
    borderRadius: borderRadius.sm,
    marginTop: spacing.sm,
  },
  disclaimerText: {
    fontSize: 11,
    color: '#92400E',
    marginLeft: 6,
    flex: 1,
    lineHeight: 15,
  },
  sectionCard: {
    marginBottom: spacing.sm,
    padding: spacing.md,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.onSurface,
    marginBottom: spacing.xs,
  },
  sectionBody: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
    lineHeight: 20,
  },
  notesCard: {
    backgroundColor: colors.surfaceContainerLow,
    borderColor: colors.border,
  },
});

export default ClinicalSummaryScreen;
