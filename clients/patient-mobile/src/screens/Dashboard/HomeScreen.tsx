import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import { consultationApi, triageApi } from '../../api';
import { Consultation, TriageResult } from '../../types';
import colors from '../../theme/colors';
import { borderRadius, shadows, spacing } from '../../theme/spacing';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import EmergencyBanner from '../../components/EmergencyBanner';

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'Home'>>();
  const { patient, user, logout, activeConsultation, setActiveConsultation, triageAlert, setTriageAlert } =
    usePatient();

  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const res = await consultationApi.listConsultations(undefined, 10, 0);
      setConsultations(res.items || []);

      // If there's an active consultation, check for any red flag triage alerts
      const active = activeConsultation || (res.items && res.items[0]);
      if (active) {
        try {
          const triage = await triageApi.getTriageResult(active.id);
          if (triage.is_red_flag || triage.priority === 'red' || triage.priority === 'EMERGENCY') {
            setTriageAlert(triage);
          }
        } catch {
          // Triage evaluation might be unavailable if intake is brand new
        }
      }
    } catch {
      // Ignore network errors on refresh
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeConsultation, setTriageAlert]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
      case 'reviewed':
        return <Badge label={status} variant="verified" />;
      case 'in_progress':
        return <Badge label="In Progress" variant="orange" />;
      case 'initiated':
      default:
        return <Badge label="Initiated" variant="yellow" />;
    }
  };

  return (
    <View style={styles.container}>
      {/* Top App Bar */}
      <View style={styles.appBar}>
        <View style={styles.brandRow}>
          <View style={styles.brandBadge}>
            <Text style={styles.brandBadgeText}>+</Text>
          </View>
          <View>
            <Text style={styles.appName}>Clinova</Text>
            <Text style={styles.welcomeText}>
              Welcome, {patient?.full_name || user?.email || 'Patient'}
            </Text>
          </View>
        </View>
        <TouchableOpacity
          onPress={() => navigation.navigate('Profile')}
          style={styles.profileBtn}
          activeOpacity={0.7}
        >
          <Ionicons name="person-circle-outline" size={32} color={colors.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />}
      >
        {/* Global Emergency Alert if red-flag detected */}
        {triageAlert && (
          <EmergencyBanner
            triageResult={triageAlert}
            onDismiss={() => setTriageAlert(null)}
          />
        )}

        {/* Start Intake Hero Card */}
        <Card elevated style={styles.heroCard}>
          <View style={styles.heroContent}>
            <View style={styles.heroTextContainer}>
              <Text style={styles.heroBadge}>CLINICAL INTAKE</Text>
              <Text style={styles.heroTitle}>Start Hospital Consultation</Text>
              <Text style={styles.heroDescription}>
                Complete AI-guided clinical history intake, scan documents, and prepare your physician summary.
              </Text>
            </View>
            <TouchableOpacity
              activeOpacity={0.8}
              style={styles.heroActionBtn}
              onPress={() => navigation.navigate('HospitalSelect')}
            >
              <Text style={styles.heroActionBtnText}>Start Intake</Text>
              <Ionicons name="arrow-forward" size={18} color={colors.onPrimary} style={{ marginLeft: 4 }} />
            </TouchableOpacity>
          </View>
        </Card>

        {/* Quick Access Action Grid */}
        <Text style={styles.sectionHeader}>Quick Access</Text>
        <View style={styles.gridRow}>
          <TouchableOpacity
            style={styles.gridCard}
            activeOpacity={0.75}
            onPress={() => navigation.navigate('Timeline')}
          >
            <View style={[styles.gridIconCircle, { backgroundColor: '#E0F2FE' }]}>
              <Ionicons name="time-outline" size={24} color="#0284C7" />
            </View>
            <Text style={styles.gridCardTitle}>Medical Timeline</Text>
            <Text style={styles.gridCardSubtitle}>Chronological events</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.gridCard}
            activeOpacity={0.75}
            onPress={() => navigation.navigate('DocumentList', {})}
          >
            <View style={[styles.gridIconCircle, { backgroundColor: '#DCFCE7' }]}>
              <Ionicons name="document-text-outline" size={24} color="#16A34A" />
            </View>
            <Text style={styles.gridCardTitle}>Medical Docs</Text>
            <Text style={styles.gridCardSubtitle}>OCR & extractions</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.gridRow}>
          <TouchableOpacity
            style={styles.gridCard}
            activeOpacity={0.75}
            onPress={() => {
              const active = activeConsultation || consultations[0];
              if (active) {
                navigation.navigate('ClinicalSummary', { consultationId: active.id });
              } else {
                navigation.navigate('HospitalSelect');
              }
            }}
          >
            <View style={[styles.gridIconCircle, { backgroundColor: '#F3E8FF' }]}>
              <Ionicons name="clipboard-outline" size={24} color="#9333EA" />
            </View>
            <Text style={styles.gridCardTitle}>Clinical Summary</Text>
            <Text style={styles.gridCardSubtitle}>Physician review draft</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.gridCard}
            activeOpacity={0.75}
            onPress={() => navigation.navigate('Profile')}
          >
            <View style={[styles.gridIconCircle, { backgroundColor: '#FEF3C7' }]}>
              <Ionicons name="person-outline" size={24} color="#D97706" />
            </View>
            <Text style={styles.gridCardTitle}>Patient Profile</Text>
            <Text style={styles.gridCardSubtitle}>Demographics & ABHA</Text>
          </TouchableOpacity>
        </View>

        {/* Existing Consultations Section */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionHeader}>Recent Consultations</Text>
          <TouchableOpacity onPress={() => navigation.navigate('HospitalSelect')}>
            <Text style={styles.sectionActionText}>+ New</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <ActivityIndicator size="small" color={colors.primary} style={{ marginVertical: spacing.lg }} />
        ) : consultations.length === 0 ? (
          <Card style={styles.emptyConsultationsCard}>
            <Ionicons name="calendar-outline" size={32} color={colors.textMuted} />
            <Text style={styles.emptyConsultationsTitle}>No Consultations Yet</Text>
            <Text style={styles.emptyConsultationsSubtitle}>
              Select a hospital and start your pre-consultation clinical intake.
            </Text>
          </Card>
        ) : (
          consultations.map((c) => (
            <TouchableOpacity
              key={c.id}
              activeOpacity={0.8}
              onPress={() => {
                setActiveConsultation(c);
                navigation.navigate('ClinicalSummary', { consultationId: c.id });
              }}
            >
              <Card style={styles.consultationCard}>
                <View style={styles.consultationHeader}>
                  <View style={styles.consultationIdRow}>
                    <Ionicons name="medkit" size={16} color={colors.primary} />
                    <Text style={styles.consultationId}>
                      Consultation #{c.id.substring(0, 8)}
                    </Text>
                  </View>
                  {getStatusBadge(c.status)}
                </View>

                {c.chief_complaint ? (
                  <Text style={styles.chiefComplaint} numberOfLines={2}>
                    Complaint: {c.chief_complaint}
                  </Text>
                ) : (
                  <Text style={styles.chiefComplaintPlaceholder}>
                    Clinical history intake in progress
                  </Text>
                )}

                <View style={styles.consultationFooter}>
                  <Text style={styles.consultationDate}>
                    Started: {new Date(c.created_at).toLocaleDateString()}
                  </Text>
                  <View style={styles.viewDetailsRow}>
                    <Text style={styles.viewDetailsText}>View Summary</Text>
                    <Ionicons name="chevron-forward" size={14} color={colors.primary} />
                  </View>
                </View>
              </Card>
            </TouchableOpacity>
          ))
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
  appBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl,
    paddingBottom: spacing.md,
    backgroundColor: colors.surfaceContainerLowest,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  brandBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
  },
  brandBadgeText: {
    color: colors.onPrimary,
    fontSize: 24,
    fontWeight: '700',
    lineHeight: 28,
  },
  appName: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.primary,
    letterSpacing: -0.5,
  },
  welcomeText: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.textSecondary,
  },
  profileBtn: {
    padding: spacing.xs,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
  heroCard: {
    backgroundColor: colors.primaryDark,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
  },
  heroContent: {},
  heroTextContainer: {
    marginBottom: spacing.md,
  },
  heroBadge: {
    fontSize: 10,
    fontWeight: '800',
    color: colors.secondaryContainer,
    letterSpacing: 1,
    marginBottom: spacing.xs,
  },
  heroTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: spacing.xs,
  },
  heroDescription: {
    fontSize: 13,
    color: '#D1FAE5',
    lineHeight: 18,
  },
  heroActionBtn: {
    backgroundColor: colors.secondaryContainer,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm + 2,
    borderRadius: borderRadius.md,
  },
  heroActionBtnText: {
    color: colors.onSecondaryContainer,
    fontSize: 14,
    fontWeight: '700',
  },
  sectionHeader: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.onSurface,
    marginBottom: spacing.sm,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  sectionActionText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.primary,
  },
  gridRow: {
    flexDirection: 'row',
    marginBottom: spacing.md,
    gap: spacing.md,
  },
  gridCard: {
    flex: 1,
    backgroundColor: colors.cardBg,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.subtle,
  },
  gridIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  gridCardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.onSurface,
  },
  gridCardSubtitle: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
  },
  emptyConsultationsCard: {
    alignItems: 'center',
    padding: spacing.xl,
  },
  emptyConsultationsTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.onSurface,
    marginTop: spacing.sm,
  },
  emptyConsultationsSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 4,
  },
  consultationCard: {
    marginBottom: spacing.sm,
    padding: spacing.md,
  },
  consultationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  consultationIdRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  consultationId: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.onSurface,
    marginLeft: 6,
  },
  chiefComplaint: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
    marginTop: 4,
    lineHeight: 18,
  },
  chiefComplaintPlaceholder: {
    fontSize: 13,
    color: colors.textMuted,
    fontStyle: 'italic',
    marginTop: 4,
  },
  consultationFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
    paddingTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  consultationDate: {
    fontSize: 11,
    color: colors.textSecondary,
  },
  viewDetailsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewDetailsText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
  },
});

export default HomeScreen;
