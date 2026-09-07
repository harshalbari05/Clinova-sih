import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { colors, spacing, borderRadius, typography, shadows } from '../constants/theme';
import { Header } from '../components/common/Header';
import { Badge } from '../components/common/Badge';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useConsultation } from '../context/ConsultationContext';
import { TimelineEvent, DatePrecision } from '../types';

interface TimelineScreenProps {
  navigation?: any;
  onNavigateToDocuments?: () => void;
  onNavigateToIntake?: () => void;
}

type EventFilter = 'ALL' | 'DIAGNOSIS' | 'MEDICATION' | 'LAB' | 'ENCOUNTER';

export const TimelineScreen: React.FC<TimelineScreenProps> = ({
  navigation,
  onNavigateToDocuments,
  onNavigateToIntake,
}) => {
  const { patient } = useAuth();
  const { consultation } = useConsultation();

  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRebuilding, setIsRebuilding] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [activeFilter, setActiveFilter] = useState<EventFilter>('ALL');

  // Load timeline
  const loadTimeline = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await apiService.getTimeline();
      setEvents(res.items || []);
    } catch {
      setEvents([]);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadTimeline();
  }, [loadTimeline]);

  const onRefresh = () => {
    setRefreshing(true);
    loadTimeline();
  };

  // Rebuild timeline from server sources
  const handleRebuildTimeline = async () => {
    try {
      setIsRebuilding(true);
      const res = await apiService.rebuildTimeline();
      setEvents(res.items || []);
      Alert.alert(
        'Timeline Synchronized',
        'Your medical timeline has been refreshed and aligned with all recorded documents and clinical visits.'
      );
    } catch {
      Alert.alert(
        'Sync Failed',
        'Could not synchronize timeline at this moment. Showing latest stored records.'
      );
    } finally {
      setIsRebuilding(false);
    }
  };

  // Format date according to backend DatePrecision
  const formatEventDate = (dateStr: string, precision: DatePrecision): string => {
    if (!dateStr) return 'Date unknown';
    const d = new Date(dateStr);
    const isValid = !isNaN(d.getTime());

    switch (precision) {
      case 'EXACT':
        return isValid
          ? d.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })
          : dateStr;
      case 'MONTH':
        return isValid
          ? d.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
          : dateStr.slice(0, 7);
      case 'YEAR':
        return isValid ? `${d.getFullYear()}` : dateStr.slice(0, 4);
      case 'APPROXIMATE':
        const yr = isValid ? `${d.getFullYear()}` : dateStr.slice(0, 4);
        return `~${yr}`;
      case 'UNKNOWN':
      default:
        return 'Date approximate';
    }
  };

  // Filter events
  const filteredEvents = events.filter((ev) => {
    if (activeFilter === 'ALL') return true;
    const type = (ev.event_type || '').toUpperCase();
    if (activeFilter === 'DIAGNOSIS') return type.includes('DIAGNOS');
    if (activeFilter === 'MEDICATION') return type.includes('MED');
    if (activeFilter === 'LAB') return type.includes('LAB') || type.includes('TEST');
    if (activeFilter === 'ENCOUNTER') return type.includes('ENCOUNTER') || type.includes('VISIT');
    return true;
  });

  const getEventIcon = (eventType: string) => {
    const t = (eventType || '').toUpperCase();
    if (t.includes('DIAGNOS')) return '🩺';
    if (t.includes('MED')) return '💊';
    if (t.includes('LAB') || t.includes('TEST')) return '🔬';
    if (t.includes('SURGERY') || t.includes('PROCEDURE')) return '🩹';
    if (t.includes('ENCOUNTER') || t.includes('VISIT')) return '🏥';
    return '📋';
  };

  return (
    <View style={styles.container}>
      <Header
        title="CLINOVA"
        subtitle="Health Timeline"
        showBack={true}
        onBackPress={() => navigation?.goBack?.() || onNavigateToIntake?.()}
        hospitalToken={consultation?.token_number ? `#${consultation.token_number}` : undefined}
      />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Banner Section */}
        <View style={styles.heroBanner}>
          <View style={styles.heroTopRow}>
            <View style={styles.heroBadgeRow}>
              <Text style={{ fontSize: 14, marginRight: 4 }}>📈</Text>
              <Text style={styles.heroBadgeText}>CHRONOLOGICAL HEALTH RECORD</Text>
            </View>
            <TouchableOpacity
              style={styles.syncBtn}
              onPress={handleRebuildTimeline}
              disabled={isRebuilding}
            >
              {isRebuilding ? (
                <ActivityIndicator size="small" color={colors.primary} />
              ) : (
                <Text style={styles.syncBtnText}>🔄 Sync Records</Text>
              )}
            </TouchableOpacity>
          </View>
          <Text style={styles.heroTitle}>Your Medical Journey</Text>
          <Text style={styles.heroSubtitle}>
            Aggregated timeline reconstructed from verified doctor prescriptions, hospital OPD visits,
            and diagnostic lab reports.
          </Text>
        </View>

        {/* Filter Chips */}
        <View style={styles.filterSection}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterRow}>
            {[
              { key: 'ALL', label: 'All Events', count: events.length },
              {
                key: 'DIAGNOSIS',
                label: 'Diagnoses',
                count: events.filter((e) => e.event_type?.toUpperCase().includes('DIAGNOS')).length,
              },
              {
                key: 'MEDICATION',
                label: 'Medications',
                count: events.filter((e) => e.event_type?.toUpperCase().includes('MED')).length,
              },
              {
                key: 'LAB',
                label: 'Lab Tests',
                count: events.filter((e) => e.event_type?.toUpperCase().includes('LAB') || e.event_type?.toUpperCase().includes('TEST')).length,
              },
              {
                key: 'ENCOUNTER',
                label: 'Visits',
                count: events.filter((e) => e.event_type?.toUpperCase().includes('ENCOUNTER')).length,
              },
            ].map((f) => {
              const active = activeFilter === f.key;
              return (
                <TouchableOpacity
                  key={f.key}
                  style={[styles.filterChip, active && styles.filterChipActive]}
                  onPress={() => setActiveFilter(f.key as EventFilter)}
                >
                  <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>
                    {f.label}
                  </Text>
                  {f.count > 0 && (
                    <View style={[styles.countBadge, active && styles.countBadgeActive]}>
                      <Text style={[styles.countBadgeText, active && styles.countBadgeTextActive]}>
                        {f.count}
                      </Text>
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {/* Loading State */}
        {isLoading && (
          <View style={styles.emptyContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={styles.loadingText}>Fetching medical timeline from Clinova records...</Text>
          </View>
        )}

        {/* Empty State */}
        {!isLoading && filteredEvents.length === 0 && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyEmoji}>📜</Text>
            <Text style={styles.emptyTitle}>No Timeline Events Recorded</Text>
            <Text style={styles.emptySubtitle}>
              Your timeline is created automatically when you upload prescriptions, lab reports, or
              complete doctor consultations.
            </Text>
            <View style={styles.emptyActionRow}>
              <TouchableOpacity
                style={styles.emptyActionBtn}
                onPress={() => onNavigateToDocuments?.()}
              >
                <Text style={styles.emptyActionBtnText}>📄 Scan/Upload Document</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.emptyActionBtn, styles.emptyActionBtnPrimary]}
                onPress={() => onNavigateToIntake?.()}
              >
                <Text style={[styles.emptyActionBtnText, styles.emptyActionBtnPrimaryText]}>
                  Start Consultation →
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Timeline Events List */}
        {!isLoading && filteredEvents.length > 0 && (
          <View style={styles.timelineList}>
            {filteredEvents.map((item, index) => {
              const isLast = index === filteredEvents.length - 1;
              const formattedDate = formatEventDate(item.event_date, item.date_precision);
              const isVerified =
                item.verification_status === 'SOURCE_CONFIRMED' ||
                item.verification_status === 'CLINICIAN_VERIFIED' ||
                item.is_verified;

              return (
                <View key={item.id || index} style={styles.timelineItem}>
                  {/* Left Column: Date & Precision */}
                  <View style={styles.dateCol}>
                    <Text style={styles.dateLabel}>{formattedDate}</Text>
                    <Text style={styles.precisionLabel}>
                      {item.date_precision === 'APPROXIMATE'
                        ? 'Approximate'
                        : item.date_precision === 'EXACT'
                        ? 'Exact'
                        : 'Documented'}
                    </Text>
                  </View>

                  {/* Center Column: Node and Spine */}
                  <View style={styles.nodeCol}>
                    <View style={styles.nodeCircle}>
                      <Text style={{ fontSize: 13 }}>{getEventIcon(item.event_type)}</Text>
                    </View>
                    {!isLast && <View style={styles.spineLine} />}
                  </View>

                  {/* Right Column: Card Content */}
                  <View style={styles.cardCol}>
                    <View style={styles.eventCard}>
                      <View style={styles.eventCardHeader}>
                        <View style={styles.eventCardTitleCol}>
                          <Text style={styles.eventTitle}>{item.title}</Text>
                          <Text style={styles.eventTypeTag}>
                            {item.event_type?.replace(/_/g, ' ')}
                          </Text>
                        </View>
                        <Badge
                          text={isVerified ? 'Verified' : 'Unverified'}
                          variant={isVerified ? 'success' : 'neutral'}
                          size="small"
                        />
                      </View>

                      {item.description && (
                        <Text style={styles.eventDesc}>{item.description}</Text>
                      )}

                      {item.evidence_snippet && (
                        <View style={styles.evidenceBlock}>
                          <Text style={styles.evidenceTitle}>Source Evidence:</Text>
                          <Text style={styles.evidenceText}>
                            "{item.evidence_snippet}"
                          </Text>
                        </View>
                      )}

                      <View style={styles.eventFooter}>
                        <Text style={styles.sourceTag}>
                          Source: {item.source_type?.replace(/_/g, ' ') || 'Medical Document'}
                        </Text>
                      </View>
                    </View>
                  </View>
                </View>
              );
            })}
          </View>
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
  heroTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  heroBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  heroBadgeText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  syncBtn: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  syncBtnText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '700',
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
  filterSection: {
    paddingVertical: spacing.sm,
    backgroundColor: colors.surfaceContainerLowest,
    borderBottomWidth: 1,
    borderBottomColor: colors.outlineVariant,
  },
  filterRow: {
    paddingHorizontal: spacing.lg,
    gap: spacing.sm,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.full,
    backgroundColor: colors.surfaceContainerLow,
    gap: spacing.xs,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
  },
  filterChipText: {
    ...typography.labelMd,
    color: colors.onSurfaceVariant,
  },
  filterChipTextActive: {
    color: colors.onPrimary,
    fontWeight: '700',
  },
  countBadge: {
    backgroundColor: colors.surfaceContainerHigh,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: borderRadius.full,
  },
  countBadgeActive: {
    backgroundColor: colors.secondaryContainer,
  },
  countBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.onSurfaceVariant,
  },
  countBadgeTextActive: {
    color: colors.onSecondaryContainer,
  },
  emptyContainer: {
    padding: spacing.xxl,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  emptyTitle: {
    ...typography.headlineSm,
    color: colors.onSurface,
    fontWeight: '700',
    textAlign: 'center',
  },
  emptySubtitle: {
    ...typography.bodyMd,
    color: colors.onSurfaceVariant,
    textAlign: 'center',
    marginTop: spacing.xs,
    lineHeight: 20,
    maxWidth: 280,
  },
  emptyActionRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.xl,
  },
  emptyActionBtn: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
  },
  emptyActionBtnText: {
    ...typography.labelMd,
    color: colors.primary,
    fontWeight: '600',
  },
  emptyActionBtnPrimary: {
    backgroundColor: colors.primary,
  },
  emptyActionBtnPrimaryText: {
    color: colors.onPrimary,
    fontWeight: '700',
  },
  loadingText: {
    ...typography.bodyMd,
    color: colors.onSurfaceVariant,
    marginTop: spacing.md,
  },
  timelineList: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
  },
  timelineItem: {
    flexDirection: 'row',
    marginBottom: spacing.md,
  },
  dateCol: {
    width: 72,
    paddingTop: 2,
  },
  dateLabel: {
    ...typography.labelMd,
    color: colors.onSurface,
    fontWeight: '700',
  },
  precisionLabel: {
    fontSize: 10,
    color: colors.onSurfaceVariant,
    marginTop: 2,
  },
  nodeCol: {
    width: 28,
    alignItems: 'center',
  },
  nodeCircle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: colors.surfaceContainerHigh,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.primary,
    zIndex: 1,
  },
  spineLine: {
    width: 2,
    flex: 1,
    backgroundColor: colors.outlineVariant,
    marginTop: -2,
    marginBottom: -8,
  },
  cardCol: {
    flex: 1,
    marginLeft: spacing.sm,
  },
  eventCard: {
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
    ...shadows.sm,
  },
  eventCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.xs,
  },
  eventCardTitleCol: {
    flex: 1,
    marginRight: spacing.sm,
  },
  eventTitle: {
    ...typography.bodyBold,
    color: colors.onSurface,
  },
  eventTypeTag: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '600',
    marginTop: 2,
    textTransform: 'capitalize',
  },
  eventDesc: {
    ...typography.bodyMd,
    color: colors.onSurfaceVariant,
    lineHeight: 20,
    marginTop: spacing.xs,
  },
  evidenceBlock: {
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.sm,
    borderRadius: borderRadius.md,
    marginTop: spacing.sm,
  },
  evidenceTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.onSurfaceVariant,
    textTransform: 'uppercase',
  },
  evidenceText: {
    ...typography.caption,
    color: colors.onSurface,
    fontStyle: 'italic',
    marginTop: 2,
  },
  eventFooter: {
    marginTop: spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sourceTag: {
    fontSize: 11,
    color: colors.onSurfaceVariant,
  },
});
