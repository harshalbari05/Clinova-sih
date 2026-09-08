import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp } from '../../navigation/types';
import { timelineApi } from '../../api';
import { TimelineEvent } from '../../types';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import EmptyState from '../../components/EmptyState';

export const TimelineScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'Timeline'>>();

  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const fetchTimeline = useCallback(async (order: 'asc' | 'desc' = sortOrder) => {
    try {
      const res = await timelineApi.getMyTimeline(order);
      setEvents(res.events || []);
    } catch {
      // Handle network error
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [sortOrder]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchTimeline();
  };

  const handleToggleOrder = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    setSortOrder(newOrder);
    setLoading(true);
    fetchTimeline(newOrder);
  };

  const handleRebuild = async () => {
    try {
      setRebuilding(true);
      const res = await timelineApi.rebuildTimeline();
      setEvents(res.events || []);
    } catch {
      // Handle rebuild error
    } finally {
      setRebuilding(false);
    }
  };

  const getVerificationBadge = (status: string) => {
    switch (status) {
      case 'CLINICIAN_VERIFIED':
        return <Badge label="Clinician Verified" variant="clinician" />;
      case 'SOURCE_CONFIRMED':
        return <Badge label="Source Confirmed" variant="verified" />;
      case 'UNVERIFIED':
      default:
        return <Badge label="Unverified" variant="unverified" />;
    }
  };

  return (
    <View style={styles.container}>
      <Header
        title="Medical Timeline"
        onBack={() => navigation.goBack()}
        rightAction={
          <View style={styles.headerActions}>
            <TouchableOpacity onPress={handleToggleOrder} style={styles.actionIconBtn}>
              <Ionicons
                name={sortOrder === 'asc' ? 'arrow-up' : 'arrow-down'}
                size={20}
                color={colors.primary}
              />
            </TouchableOpacity>
            <TouchableOpacity
              onPress={handleRebuild}
              disabled={rebuilding}
              style={[styles.actionIconBtn, { marginLeft: 8 }]}
            >
              {rebuilding ? (
                <ActivityIndicator size="small" color={colors.primary} />
              ) : (
                <Ionicons name="sync-outline" size={20} color={colors.primary} />
              )}
            </TouchableOpacity>
          </View>
        }
      />

      <View style={styles.subHeader}>
        <Text style={styles.subHeaderText}>
          Chronological medical events extracted from intake responses & documents.
        </Text>
      </View>

      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Building chronological timeline...</Text>
        </View>
      ) : events.length === 0 ? (
        <EmptyState
          icon="time-outline"
          title="Timeline is Empty"
          description="Complete your clinical interview or upload medical documents to generate your medical timeline."
          actionTitle="Rebuild Timeline"
          onAction={handleRebuild}
        />
      ) : (
        <FlatList
          data={events}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />
          }
          renderItem={({ item, index }) => (
            <View style={styles.timelineRow}>
              {/* Timeline spine and node */}
              <View style={styles.spineCol}>
                <View style={styles.spineNode} />
                {index < events.length - 1 && <View style={styles.spineLine} />}
              </View>

              {/* Event Card */}
              <View style={styles.cardCol}>
                <Card style={styles.eventCard}>
                  <View style={styles.eventHeader}>
                    <Text style={styles.eventDate}>
                      {item.event_date ? new Date(item.event_date).toLocaleDateString() : 'Undated'}
                    </Text>
                    {getVerificationBadge(item.verification_status)}
                  </View>

                  <Text style={styles.eventTitle}>{item.title}</Text>

                  {item.description ? (
                    <Text style={styles.eventDescription}>{item.description}</Text>
                  ) : null}

                  {item.evidence_snippet ? (
                    <View style={styles.evidenceBox}>
                      <Ionicons name="document-text-outline" size={14} color={colors.textSecondary} />
                      <Text style={styles.evidenceText} numberOfLines={2}>
                        Evidence: "{item.evidence_snippet}"
                      </Text>
                    </View>
                  ) : null}

                  <View style={styles.sourceFooter}>
                    <Text style={styles.sourceText}>
                      Source: {item.source_type.replace('_', ' ').toUpperCase()}
                    </Text>
                  </View>
                </Card>
              </View>
            </View>
          )}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionIconBtn: {
    padding: spacing.xs,
  },
  subHeader: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    backgroundColor: colors.surfaceContainerLow,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  subHeaderText: {
    fontSize: 12,
    color: colors.textSecondary,
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
  listContent: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
  timelineRow: {
    flexDirection: 'row',
  },
  spineCol: {
    alignItems: 'center',
    width: 24,
    marginRight: spacing.sm,
  },
  spineNode: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: colors.primary,
    marginTop: spacing.md,
  },
  spineLine: {
    flex: 1,
    width: 2,
    backgroundColor: colors.border,
  },
  cardCol: {
    flex: 1,
    marginBottom: spacing.md,
  },
  eventCard: {
    padding: spacing.md,
  },
  eventHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  eventDate: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primary,
  },
  eventTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.onSurface,
  },
  eventDescription: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
    lineHeight: 18,
    marginTop: 4,
  },
  evidenceBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.xs + 2,
    borderRadius: borderRadius.sm,
    marginTop: spacing.xs,
  },
  evidenceText: {
    fontSize: 11,
    fontStyle: 'italic',
    color: colors.textSecondary,
    marginLeft: 4,
    flex: 1,
  },
  sourceFooter: {
    marginTop: spacing.xs,
    paddingTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  sourceText: {
    fontSize: 10,
    color: colors.textMuted,
    fontWeight: '600',
  },
});

export default TimelineScreen;
