/**
 * Mobile Home / Dashboard Screen
 * Faithfully matches clinova_patient_dashboard design.
 */
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  SafeAreaView,
} from 'react-native';
import { colors, typography, spacing, borderRadius, shadows } from '../constants/theme';
import { Header } from '../components/common/Header';
import { Badge } from '../components/common/Badge';
import { useAuth } from '../context/AuthContext';
import { useConsultation } from '../context/ConsultationContext';
import { api } from '../services/api';
import { MedicalDocument } from '../types';

interface HomeScreenProps {
  navigation?: any;
  onNavigateToIntake?: () => void;
  onStartConsultation?: () => void;
  onNavigateToDocuments?: () => void;
  onNavigateToTimeline?: () => void;
  onNavigateToSummary?: () => void;
  onNavigateToProfile?: () => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  navigation,
  onNavigateToIntake,
  onStartConsultation,
  onNavigateToDocuments,
  onNavigateToTimeline,
  onNavigateToSummary,
  onNavigateToProfile,
}) => {
  const handleIntake = onStartConsultation || onNavigateToIntake || (() => navigation?.navigate?.('Intake'));
  const handleDocs = onNavigateToDocuments || (() => navigation?.navigate?.('Documents'));
  const handleTimeline = onNavigateToTimeline || (() => navigation?.navigate?.('Timeline'));
  const handleSummary = onNavigateToSummary || (() => navigation?.navigate?.('Summary'));
  const handleProfile = onNavigateToProfile || (() => navigation?.navigate?.('Profile'));
  const { patient } = useAuth();
  const { activeConsultation, selectedHospital, loadHospitals } = useConsultation();

  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [documents, setDocuments] = useState<MedicalDocument[]>([]);

  const loadDashboardData = async () => {
    try {
      await loadHospitals();
      const docs = await api.getMyDocuments();
      setDocuments(docs.slice(0, 3));
    } catch {
      // Safe dashboard load fallback
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const patientName = patient?.full_name || 'Rahul Sharma';
  const initials = patientName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const tokenNumber = activeConsultation?.token_number || '24';
  const departmentName = activeConsultation?.department || 'General Medicine';
  const hospitalName = selectedHospital?.name || 'City Hospital OPD';

  return (
    <SafeAreaView style={styles.safeArea}>
      <Header
        title="CLINOVA"
        subtitle="Patient Portal"
        patientInitials={initials}
        onProfilePress={onNavigateToProfile}
        onNotificationPress={() => {}}
      />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        showsVerticalScrollIndicator={false}
      >
        {/* 1. Welcome Section */}
        <View style={styles.welcomeSection}>
          <View style={styles.welcomeTextColumn}>
            <Text style={styles.welcomeTitle}>Good morning, {patientName.split(' ')[0]}</Text>
            <Text style={styles.welcomeSubtitle}>
              Welcome to Clinova. Let's get you ready for your hospital visit.
            </Text>
          </View>
          <View style={styles.opdBadge}>
            <View style={styles.greenDot} />
            <Text style={styles.opdBadgeText}>OPD Today</Text>
          </View>
        </View>

        {/* 2. Priority Action Card (Gradient Teal Card) */}
        <View style={styles.priorityCard}>
          <View style={styles.priorityHeaderRow}>
            <View style={styles.priorityPill}>
              <Text style={styles.priorityPillText}>Priority Step</Text>
            </View>
            <Text style={styles.stepsRemainingText}>2 Steps Remaining</Text>
          </View>

          <Text style={styles.priorityCardTitle}>Prepare for your consultation</Text>

          {/* Progress Indicator */}
          <View style={styles.progressContainer}>
            <View style={styles.progressLabelRow}>
              <Text style={styles.progressLabel}>Your information is 65% complete</Text>
              <Text style={styles.progressPercentage}>65%</Text>
            </View>
            <View style={styles.progressBarBackground}>
              <View style={[styles.progressBarFill, { width: '65%' }]} />
            </View>
          </View>

          <Text style={styles.priorityCardSubtext}>
            Complete your medical information before meeting your doctor.
          </Text>

          <TouchableOpacity
            onPress={onNavigateToIntake}
            style={styles.continueButton}
            accessibilityRole="button"
          >
            <Text style={styles.continueButtonText}>Continue Medical History →</Text>
          </TouchableOpacity>
        </View>

        {/* 3. Consultation / Visit Status Card */}
        <View style={styles.visitCard}>
          <View style={styles.visitCardHeader}>
            <View style={styles.visitTitleRow}>
              <View style={styles.tealDot} />
              <Text style={styles.visitCardTitle}>My Hospital Visit</Text>
            </View>
            <Badge label="Ready for Consultation" type="success" dot />
          </View>

          <View style={styles.visitDetailsBox}>
            <View style={styles.visitRow}>
              <View style={styles.visitInfoColumn}>
                <Text style={styles.hospitalNameText}>{hospitalName}</Text>
                <Text style={styles.departmentText}>Department: {departmentName}</Text>
                <Text style={styles.roomText}>Room 204 • General OPD Wing B</Text>
              </View>

              <View style={styles.tokenBox}>
                <Text style={styles.tokenLabel}>TOKEN NO.</Text>
                <Text style={styles.tokenNumber}>{tokenNumber}</Text>
              </View>
            </View>

            <View style={styles.queueFooterRow}>
              <View style={styles.queueInfoRow}>
                <Text style={styles.queueIcon}>🏥</Text>
                <View>
                  <Text style={styles.queueTitle}>Department OPD Queue</Text>
                  <Text style={styles.queueSubtitle}>Assigned by Next Available Physician</Text>
                </View>
              </View>
              <View style={styles.timeColumn}>
                <Text style={styles.timeText}>Today • 10:30 AM</Text>
                <Text style={styles.waitText}>Estimated wait: ~15 mins</Text>
              </View>
            </View>
          </View>

          <TouchableOpacity onPress={onNavigateToSummary} style={styles.viewDetailsButton}>
            <Text style={styles.viewDetailsText}>View Consultation Details →</Text>
          </TouchableOpacity>
        </View>

        {/* 4. Quick Actions (2x2 Grid) */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>What would you like to do?</Text>
          <Text style={styles.sectionSubtitle}>Quick access</Text>
        </View>

        <View style={styles.quickActionsGrid}>
          {/* Action 1: Medical History */}
          <TouchableOpacity onPress={onNavigateToIntake} style={styles.actionTile}>
            <View style={[styles.tileIconCircle, { backgroundColor: colors.primaryLight }]}>
              <Text style={styles.tileEmoji}>🩺</Text>
            </View>
            <Text style={styles.tileTitle}>Medical History</Text>
            <Text style={styles.tileDesc}>Add or update my health information</Text>
          </TouchableOpacity>

          {/* Action 2: Medical Documents */}
          <TouchableOpacity onPress={onNavigateToDocuments} style={styles.actionTile}>
            <View style={[styles.tileIconCircle, { backgroundColor: '#E0F2FE' }]}>
              <Text style={styles.tileEmoji}>📄</Text>
            </View>
            <Text style={styles.tileTitle}>Medical Documents</Text>
            <Text style={styles.tileDesc}>Scan or upload reports & prescriptions</Text>
          </TouchableOpacity>

          {/* Action 3: Review Information */}
          <TouchableOpacity onPress={onNavigateToSummary} style={styles.actionTile}>
            <View style={[styles.tileIconCircle, { backgroundColor: '#EEF2FF' }]}>
              <Text style={styles.tileEmoji}>👁️</Text>
            </View>
            <Text style={styles.tileTitle}>Review Information</Text>
            <Text style={styles.tileDesc}>Check the information I have provided</Text>
          </TouchableOpacity>

          {/* Action 4: Medical Timeline */}
          <TouchableOpacity onPress={onNavigateToTimeline} style={styles.actionTile}>
            <View style={[styles.tileIconCircle, { backgroundColor: '#FEF3C7' }]}>
              <Text style={styles.tileEmoji}>📅</Text>
            </View>
            <Text style={styles.tileTitle}>Health Timeline</Text>
            <Text style={styles.tileDesc}>Chronological health events & history</Text>
          </TouchableOpacity>
        </View>

        {/* 5. Medical Information Completion Checklist */}
        <View style={styles.checklistCard}>
          <View style={styles.checkHeader}>
            <View>
              <Text style={styles.checkTitle}>My Medical Information</Text>
              <Text style={styles.checkSubtitle}>Keep your doctor informed for safer care</Text>
            </View>
            <Badge label="2 of 5 done" type="priority" />
          </View>

          <View style={styles.checkItemsWrapper}>
            <View style={styles.checkItem}>
              <View style={styles.checkLeft}>
                <Text style={styles.checkCheck}>✓</Text>
                <Text style={styles.checkItemLabel}>Basic Information</Text>
              </View>
              <Badge label="Complete" type="success" />
            </View>

            <View style={styles.checkItem}>
              <View style={styles.checkLeft}>
                <Text style={styles.checkCheck}>✓</Text>
                <Text style={styles.checkItemLabel}>Symptoms & Current Problem</Text>
              </View>
              <Badge label="Complete" type="success" />
            </View>

            <View style={styles.checkItem}>
              <View style={styles.checkLeft}>
                <Text style={styles.checkCircle}>○</Text>
                <Text style={styles.checkItemLabel}>Past Medical History</Text>
              </View>
              <Badge label="Incomplete" type="neutral" />
            </View>

            <View style={styles.checkItem}>
              <View style={styles.checkLeft}>
                <Text style={styles.checkCircle}>○</Text>
                <Text style={styles.checkItemLabel}>Medicines & Allergies</Text>
              </View>
              <Badge label="Incomplete" type="neutral" />
            </View>

            <View style={styles.checkItem}>
              <View style={styles.checkLeft}>
                <Text style={styles.checkCircle}>○</Text>
                <Text style={styles.checkItemLabel}>Family History</Text>
              </View>
              <Badge label="Incomplete" type="neutral" />
            </View>
          </View>

          <TouchableOpacity onPress={onNavigateToIntake} style={styles.completeHistoryBtn}>
            <Text style={styles.completeHistoryBtnText}>Complete Medical History →</Text>
          </TouchableOpacity>
        </View>

        {/* 6. ABHA Digital Health Card */}
        <View style={styles.abhaCard}>
          <View style={styles.abhaLeft}>
            <View style={styles.abhaBadge}>
              <Text style={styles.abhaBadgeText}>ABHA</Text>
            </View>
            <View>
              <View style={styles.abhaTitleRow}>
                <Text style={styles.abhaTitle}>Ayushman Bharat Health Account</Text>
                <Badge label="Connected" type="success" dot />
              </View>
              <Text style={styles.abhaNumber}>{patient?.abha_id || '91-4521-8890-1234'}</Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: 40,
  },
  welcomeSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
    paddingTop: 4,
  },
  welcomeTextColumn: {
    flex: 1,
    paddingRight: spacing.sm,
  },
  welcomeTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.textPrimary,
    letterSpacing: -0.3,
  },
  welcomeSubtitle: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textMuted,
    marginTop: 2,
    lineHeight: 18,
  },
  opdBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: colors.primaryLight,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
  },
  greenDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.emerald,
  },
  opdBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primary,
  },
  priorityCard: {
    backgroundColor: colors.primaryDark,
    borderRadius: borderRadius.xxl,
    padding: spacing.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(0, 104, 95, 0.4)',
    ...shadows.elevated,
  },
  priorityHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  priorityPill: {
    backgroundColor: 'rgba(20, 184, 166, 0.25)',
    borderWidth: 1,
    borderColor: 'rgba(204, 251, 241, 0.3)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
  },
  priorityPillText: {
    color: '#CCFBF1',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  stepsRemainingText: {
    color: '#99EFE5',
    fontSize: 12,
    fontWeight: '700',
  },
  priorityCardTitle: {
    fontSize: 19,
    fontWeight: '800',
    color: colors.textLight,
    lineHeight: 24,
    marginBottom: spacing.md,
  },
  progressContainer: {
    marginBottom: spacing.sm,
  },
  progressLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  progressLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#CCFBF1',
  },
  progressPercentage: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.textLight,
  },
  progressBarBackground: {
    height: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderRadius: borderRadius.full,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: colors.emerald,
    borderRadius: borderRadius.full,
  },
  priorityCardSubtext: {
    fontSize: 12,
    color: '#CCFBF1',
    marginBottom: spacing.md,
    lineHeight: 16,
  },
  continueButton: {
    backgroundColor: colors.surface,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.card,
  },
  continueButtonText: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.primaryDark,
  },
  visitCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
    ...shadows.card,
  },
  visitCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  visitTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tealDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.primary,
  },
  visitCardTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  visitDetailsBox: {
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.sm,
  },
  visitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  visitInfoColumn: {
    flex: 1,
    paddingRight: spacing.sm,
  },
  hospitalNameText: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  departmentText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primary,
    marginTop: 2,
  },
  roomText: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  tokenBox: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
    borderRadius: borderRadius.md,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  tokenLabel: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.textMuted,
    letterSpacing: 0.5,
  },
  tokenNumber: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.primary,
  },
  queueFooterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.sm,
  },
  queueInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  queueIcon: {
    fontSize: 18,
  },
  queueTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  queueSubtitle: {
    fontSize: 10,
    color: colors.textMuted,
  },
  timeColumn: {
    alignItems: 'flex-end',
  },
  timeText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primary,
  },
  waitText: {
    fontSize: 10,
    color: colors.textMuted,
  },
  viewDetailsButton: {
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.primaryBorder,
    borderRadius: borderRadius.md,
  },
  viewDetailsText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primary,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: spacing.sm,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  sectionSubtitle: {
    fontSize: 11,
    color: colors.textMuted,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  actionTile: {
    width: '48.5%',
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.card,
  },
  tileIconCircle: {
    width: 38,
    height: 38,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  tileEmoji: {
    fontSize: 18,
  },
  tileTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  tileDesc: {
    fontSize: 11,
    color: colors.textMuted,
    lineHeight: 14,
  },
  checklistCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
    ...shadows.card,
  },
  checkHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  checkTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  checkSubtitle: {
    fontSize: 11,
    color: colors.textMuted,
  },
  checkItemsWrapper: {
    borderWidth: 1,
    borderColor: colors.borderSubtle,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
    marginBottom: spacing.md,
  },
  checkItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.sm + 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
  },
  checkLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  checkCheck: {
    color: colors.emerald,
    fontWeight: '900',
    fontSize: 14,
  },
  checkCircle: {
    color: colors.textSubtle,
    fontSize: 14,
  },
  checkItemLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  completeHistoryBtn: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm + 2,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  completeHistoryBtnText: {
    color: colors.textLight,
    fontSize: 12,
    fontWeight: '700',
  },
  abhaCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  abhaLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  abhaBadge: {
    width: 42,
    height: 42,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primaryLight,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },
  abhaBadgeText: {
    fontSize: 11,
    fontWeight: '900',
    color: colors.primary,
  },
  abhaTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 2,
  },
  abhaTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  abhaNumber: {
    fontSize: 11,
    fontFamily: 'Courier',
    color: colors.textMuted,
  },
});
