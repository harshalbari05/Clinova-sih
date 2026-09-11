/**
 * HomeScreen — Patient Dashboard
 *
 * Designed for elderly, rural, low-literacy patients.
 * Large touch targets, icon + text, bilingual labels, minimal options.
 *
 * 7 Actions:
 *  1. Talk to Clinova (AI interview)
 *  2. Add Medical Report (document upload)
 *  3. My Health Summary
 *  4. My Medical History (timeline)
 *  5. Hospital Visit / Token
 *  6. My QR Code
 *  7. My Profile
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import { consultationApi, triageApi, patientApi } from '../../api';
import { Consultation, TriageResult, ActiveVisit } from '../../types';
import colors from '../../theme/colors';
import { borderRadius, shadows, spacing } from '../../theme/spacing';
import Card from '../../components/Card';
import EmergencyBanner from '../../components/EmergencyBanner';

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'Home'>>();
  const {
    patient,
    user,
    language,
    activeConsultation,
    setActiveConsultation,
    triageAlert,
    setTriageAlert,
    logout,
  } = usePatient();

  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [activeVisit, setActiveVisit] = useState<ActiveVisit | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshingVisit, setRefreshingVisit] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [res, visit] = await Promise.allSettled([
        consultationApi.listConsultations(undefined, 10, 0),
        patientApi.getActiveVisit(),
      ]);

      if (res.status === 'fulfilled') {
        setConsultations(res.value.items || []);
        const active = activeConsultation || (res.value.items && res.value.items[0]);
        if (active) {
          try {
            const triage = await triageApi.getTriageResult(active.id);
            if (triage.is_red_flag || triage.priority === 'red' || triage.priority === 'EMERGENCY') {
              setTriageAlert(triage);
            }
          } catch {
            // Triage may not exist yet
          }
        }
      }

      if (visit.status === 'fulfilled') {
        setActiveVisit(visit.value);
      }
    } catch {
      // Ignore network errors on load
    } finally {
      setLoading(false);
      setRefreshing(false);
      setRefreshingVisit(false);
    }
  }, [activeConsultation, setTriageAlert]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Polling every 7 seconds to keep token and Now Serving state updated
  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const visit = await patientApi.getActiveVisit();
        setActiveVisit(visit);
      } catch {
        // Ignore
      }
    }, 7000);
    return () => clearInterval(timer);
  }, []);

  const refreshActiveVisit = async () => {
    try {
      setRefreshingVisit(true);
      const visit = await patientApi.getActiveVisit();
      setActiveVisit(visit);
    } catch {
      // Ignore
    } finally {
      setRefreshingVisit(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  /**
   * "Talk to Clinova" — creates a consultation (without hospital) and enters interview.
   */
  const handleTalkToClinova = async () => {
    try {
      // If there is already an active (non-completed) consultation, resume it
      const resumable = consultations.find(
        (c) => c.status === 'initiated' || c.status === 'in_progress'
      );
      const consultation = resumable || activeConsultation;

      if (consultation) {
        await setActiveConsultation(consultation);
        navigation.navigate('LanguageSelect', { consultationId: consultation.id });
      } else {
        // Create a new consultation — hospital_id assigned later at reception
        const newConsultation = await consultationApi.createConsultation({
          chief_complaint: 'Clinical intake — patient initiated',
        });
        await setActiveConsultation(newConsultation);
        navigation.navigate('LanguageSelect', { consultationId: newConsultation.id });
      }
    } catch (err: any) {
      Alert.alert(
        'Connection Error',
        'Could not connect to Clinova services. Please check your internet and try again.',
        [{ text: 'OK' }]
      );
    }
  };

  /**
   * "My Health Summary" — navigate to the most recent consultation's summary
   */
  const handleHealthSummary = () => {
    const active = activeConsultation || consultations[0];
    if (active) {
      navigation.navigate('ClinicalSummary', { consultationId: active.id });
    } else {
      Alert.alert(
        'No Summary Yet',
        'Complete an AI interview first to generate your health summary.',
        [{ text: 'OK' }]
      );
    }
  };

  const displayName = patient?.full_name || user?.email || user?.phone || 'Patient';

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
            <Text style={styles.welcomeText} numberOfLines={1}>
              नमस्ते, {displayName}
            </Text>
          </View>
        </View>
        <TouchableOpacity
          onPress={() => navigation.navigate('Profile')}
          style={styles.profileBtn}
          activeOpacity={0.7}
          accessibilityLabel="My Profile"
        >
          <Ionicons name="person-circle-outline" size={36} color={colors.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />}
      >
        {/* Emergency Alert Banner */}
        {triageAlert && (
          <EmergencyBanner
            triageResult={triageAlert}
            onDismiss={() => setTriageAlert(null)}
          />
        )}

        {/* Primary Action — Talk to Clinova */}
        <TouchableOpacity
          style={styles.primaryAction}
          activeOpacity={0.85}
          onPress={handleTalkToClinova}
          accessibilityRole="button"
          accessibilityLabel="Talk to Clinova — Start AI clinical interview"
        >
          <View style={styles.primaryActionIconCircle}>
            <Ionicons name="mic" size={36} color={colors.onPrimary} />
          </View>
          <View style={styles.primaryActionText}>
            <Text style={styles.primaryActionTitle}>Clinova से बात करें</Text>
            <Text style={styles.primaryActionSubtitle}>Talk to Clinova</Text>
            <Text style={styles.primaryActionHint}>
              AI से अपने लक्षण बताएं / Tell the AI your symptoms
            </Text>
          </View>
          <Ionicons name="arrow-forward-circle" size={32} color={colors.onPrimary} style={{ opacity: 0.8 }} />
        </TouchableOpacity>

        {/* Dashboard Action Grid */}
        <Text style={styles.sectionHeader}>मेरी स्वास्थ्य सेवाएं / My Services</Text>

        <View style={styles.gridRow}>
          <DashboardCard
            icon="cloud-upload-outline"
            iconBg="#DCFCE7"
            iconColor="#16A34A"
            title="रिपोर्ट जोड़ें"
            subtitle="Add Medical Report"
            onPress={() => navigation.navigate('DocumentUpload', {})}
          />
          <DashboardCard
            icon="document-text-outline"
            iconBg="#EFF6FF"
            iconColor="#2563EB"
            title="स्वास्थ्य सारांश"
            subtitle="My Health Summary"
            onPress={handleHealthSummary}
          />
        </View>

        <View style={styles.gridRow}>
          <DashboardCard
            icon="time-outline"
            iconBg="#E0F2FE"
            iconColor="#0284C7"
            title="मेडिकल हिस्ट्री"
            subtitle="My Medical History"
            onPress={() => navigation.navigate('Timeline')}
          />
          <DashboardCard
            icon="qr-code-outline"
            iconBg="#F3E8FF"
            iconColor="#9333EA"
            title="मेरा QR कोड"
            subtitle="My QR Code"
            onPress={() => navigation.navigate('PatientQR')}
          />
        </View>

        {/* Hospital Visit / Token Card (SIH Step 3) */}
        {activeVisit && activeVisit.has_active_visit ? (
          <Card style={styles.activeVisitCard}>
            {/* Header: Department and Hospital */}
            <View style={styles.activeVisitHeader}>
              <View style={styles.activeVisitHeaderLeft}>
                <View style={styles.hospitalIconCircleActive}>
                  <Ionicons name="medical" size={22} color="#FFFFFF" />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.activeVisitTitle}>
                    {language === 'Hindi'
                      ? 'मेरी अस्पताल विजिट'
                      : language === 'Marathi'
                      ? 'माझी रुग्णालय भेट'
                      : 'My Hospital Visit'}
                  </Text>
                  <Text style={styles.activeVisitDept} numberOfLines={1}>
                    {activeVisit.department || 'General OPD'} • {activeVisit.hospital_name || 'Clinova Hospital'}
                  </Text>
                </View>
              </View>
              <TouchableOpacity
                onPress={refreshActiveVisit}
                style={styles.visitRefreshBtn}
                disabled={refreshingVisit}
                accessibilityLabel="Refresh Queue Status"
              >
                <Ionicons
                  name={refreshingVisit ? 'sync' : 'refresh'}
                  size={18}
                  color={colors.primary}
                />
              </TouchableOpacity>
            </View>

            {/* Token Hero Banner */}
            <View style={styles.tokenHighlightBox}>
              <Text style={styles.tokenLabel}>
                {language === 'Hindi'
                  ? 'आपका टोकन'
                  : language === 'Marathi'
                  ? 'तुमचा टोकन'
                  : 'Your Token'}
              </Text>
              <Text style={styles.tokenNumber}>
                {activeVisit.token_number != null ? activeVisit.token_number : '--'}
              </Text>

              {/* Status Pill */}
              <View
                style={[
                  styles.tokenStatusPill,
                  {
                    backgroundColor:
                      activeVisit.status === 'in_progress' ? '#DCFCE7' : '#FEF3C7',
                  },
                ]}
              >
                <View
                  style={[
                    styles.tokenStatusDot,
                    {
                      backgroundColor:
                        activeVisit.status === 'in_progress' ? '#16A34A' : '#D97706',
                    },
                  ]}
                />
                <Text
                  style={[
                    styles.tokenStatusPillText,
                    {
                      color:
                        activeVisit.status === 'in_progress' ? '#166534' : '#92400E',
                    },
                  ]}
                >
                  {activeVisit.status === 'in_progress'
                    ? language === 'Hindi'
                      ? 'अभी चल रहा है / अंदर जाएं'
                      : language === 'Marathi'
                      ? 'सध्या सुरू / आत जा'
                      : 'Now Serving / Your Turn'
                    : language === 'Hindi'
                    ? 'प्रतीक्षा'
                    : language === 'Marathi'
                    ? 'प्रतीक्षा'
                    : 'Waiting'}
                </Text>
              </View>
            </View>

            {/* Operational Queue Metrics: Now Serving & People Ahead */}
            <View style={styles.queueStatsRow}>
              {/* Now Serving */}
              <View style={styles.queueStatBox}>
                <View style={styles.queueStatHeader}>
                  <Ionicons name="play-circle-outline" size={16} color="#0D9488" />
                  <Text style={styles.queueStatTitle}>
                    {language === 'Hindi'
                      ? 'अभी चल रहा है'
                      : language === 'Marathi'
                      ? 'सध्या सुरू'
                      : 'Now Serving'}
                  </Text>
                </View>
                <Text style={styles.queueStatValue}>
                  {activeVisit.now_serving != null ? activeVisit.now_serving : '--'}
                </Text>
              </View>

              {/* People Ahead */}
              <View style={styles.queueStatBox}>
                <View style={styles.queueStatHeader}>
                  <Ionicons name="people-outline" size={16} color="#4F46E5" />
                  <Text style={styles.queueStatTitle}>
                    {language === 'Hindi'
                      ? 'आपसे पहले'
                      : language === 'Marathi'
                      ? 'तुमच्या आधी'
                      : 'People Ahead'}
                  </Text>
                </View>
                <Text style={styles.queueStatValue}>
                  {activeVisit.people_ahead != null ? activeVisit.people_ahead : 0}
                </Text>
              </View>
            </View>

            {/* Accessible Low-Literacy Audio/Visual Guidance */}
            <View style={styles.hospitalGuidanceRow}>
              <Ionicons name="information-circle-outline" size={16} color={colors.textSecondary} />
              <Text style={styles.hospitalGuidanceText}>
                {language === 'Hindi'
                  ? 'जब स्क्रीन पर आपका टोकन दिखे, तब ओपीडी कक्ष में प्रवेश करें।'
                  : language === 'Marathi'
                  ? 'पडद्यावर तुमचा टोकन दिसताच ओपीडी कक्षात प्रवेश करा.'
                  : 'Please proceed to the OPD room when your token is called.'}
              </Text>
            </View>
          </Card>
        ) : (
          <Card style={styles.hospitalCard}>
            <View style={styles.hospitalCardRow}>
              <View style={[styles.hospitalIconCircle, { backgroundColor: '#FEF3C7' }]}>
                <Ionicons name="medkit-outline" size={26} color="#D97706" />
              </View>
              <View style={styles.hospitalCardText}>
                <Text style={styles.hospitalCardTitle}>
                  {language === 'Hindi'
                    ? 'अस्पताल विजिट / टोकन'
                    : language === 'Marathi'
                    ? 'रुग्णालय भेट / टोकन'
                    : 'Hospital Visit / Token'}
                </Text>
                <Text style={styles.hospitalCardSubtitle}>
                  {language === 'Hindi'
                    ? 'अस्पताल रिसेप्शन पर QR कोड दिखाकर टोकन प्राप्त करें।'
                    : language === 'Marathi'
                    ? 'रुग्णालय रिसेप्शनवर QR कोड दाखवून टोकन मिळवा.'
                    : 'Token information will appear here when assigned by hospital reception.'}
                </Text>
              </View>
            </View>
            <View style={styles.hospitalStatusBadge}>
              <Ionicons name="qr-code-outline" size={14} color={colors.textSecondary} />
              <Text style={styles.hospitalStatusText}>
                {language === 'Hindi'
                  ? 'रिसेप्शन पर अपना QR कोड दिखाएं'
                  : language === 'Marathi'
                  ? 'रिसेप्शनवर आपला QR कोड दाखवा'
                  : 'Register at reception with your QR code'}
              </Text>
            </View>
          </Card>
        )}

        {/* Recent Consultations Section */}
        {!loading && consultations.length > 0 && (
          <View style={{ marginTop: spacing.md }}>
            <Text style={styles.sectionHeader}>हाल की बातचीत / Recent Sessions</Text>
            {consultations.slice(0, 3).map((c) => (
              <TouchableOpacity
                key={c.id}
                activeOpacity={0.8}
                onPress={() => {
                  setActiveConsultation(c);
                  navigation.navigate('ClinicalSummary', { consultationId: c.id });
                }}
              >
                <Card style={styles.consultationCard}>
                  <View style={styles.consultationRow}>
                    <Ionicons name="medkit-outline" size={18} color={colors.primary} />
                    <View style={styles.consultationInfo}>
                      <Text style={styles.consultationDate}>
                        {new Date(c.created_at).toLocaleDateString('en-IN', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </Text>
                      <Text style={styles.consultationComplaint} numberOfLines={1}>
                        {c.chief_complaint || 'Clinical intake session'}
                      </Text>
                    </View>
                    <Ionicons name="chevron-forward" size={18} color={colors.primary} />
                  </View>
                </Card>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {loading && (
          <ActivityIndicator size="small" color={colors.primary} style={{ marginVertical: spacing.lg }} />
        )}
      </ScrollView>
    </View>
  );
};

/* ─── Dashboard Card Component ─── */
interface DashboardCardProps {
  icon: any;
  iconBg: string;
  iconColor: string;
  title: string;
  subtitle: string;
  onPress: () => void;
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  icon, iconBg, iconColor, title, subtitle, onPress,
}) => (
  <TouchableOpacity
    style={styles.gridCard}
    activeOpacity={0.75}
    onPress={onPress}
    accessibilityRole="button"
    accessibilityLabel={`${subtitle} — ${title}`}
  >
    <View style={[styles.gridIconCircle, { backgroundColor: iconBg }]}>
      <Ionicons name={icon} size={28} color={iconColor} />
    </View>
    <Text style={styles.gridCardTitleHindi}>{title}</Text>
    <Text style={styles.gridCardSubtitle}>{subtitle}</Text>
  </TouchableOpacity>
);

/* ─── Styles ─── */
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
    flex: 1,
    marginRight: spacing.sm,
  },
  brandBadge: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
    flexShrink: 0,
  },
  brandBadgeText: {
    color: colors.onPrimary,
    fontSize: 26,
    fontWeight: '700',
    lineHeight: 30,
  },
  appName: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.primary,
    letterSpacing: -0.5,
  },
  welcomeText: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textSecondary,
    maxWidth: 200,
  },
  profileBtn: {
    padding: spacing.xs,
    flexShrink: 0,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: 40,
  },
  // Primary CTA
  primaryAction: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    ...shadows.subtle,
  },
  primaryActionIconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
    flexShrink: 0,
  },
  primaryActionText: {
    flex: 1,
    marginRight: spacing.sm,
  },
  primaryActionTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.onPrimary,
  },
  primaryActionSubtitle: {
    fontSize: 14,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.85)',
    marginTop: 2,
  },
  primaryActionHint: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.65)',
    marginTop: 3,
    lineHeight: 16,
  },
  sectionHeader: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.onSurface,
    marginBottom: spacing.sm,
    marginTop: spacing.xs,
  },
  // Grid
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
    minHeight: 110,
  },
  gridIconCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  gridCardTitleHindi: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.onSurface,
    lineHeight: 18,
  },
  gridCardSubtitle: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
  },
  // Hospital Visit card
  hospitalCard: {
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  hospitalCardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  hospitalIconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
    flexShrink: 0,
  },
  hospitalCardText: {
    flex: 1,
  },
  hospitalCardTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.onSurface,
  },
  hospitalCardSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
    lineHeight: 16,
  },
  hospitalStatusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerLow,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
    borderRadius: borderRadius.sm,
    marginTop: spacing.xs,
  },
  hospitalStatusText: {
    fontSize: 11,
    color: colors.textSecondary,
    marginLeft: 4,
    flex: 1,
  },
  // Active Hospital Visit (SIH Step 3)
  activeVisitCard: {
    marginBottom: spacing.md,
    padding: spacing.md,
    borderWidth: 2,
    borderColor: colors.primary,
    backgroundColor: '#FFFFFF',
    borderRadius: borderRadius.lg,
    ...shadows.subtle,
  },
  activeVisitHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  activeVisitHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: spacing.sm,
  },
  hospitalIconCircleActive: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
    flexShrink: 0,
  },
  activeVisitTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.onSurface,
  },
  activeVisitDept: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.primary,
    marginTop: 1,
  },
  visitRefreshBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  tokenHighlightBox: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F0FDFA',
    borderRadius: borderRadius.md,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    marginVertical: spacing.sm,
    borderWidth: 1,
    borderColor: '#CCFBF1',
  },
  tokenLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0F766E',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  tokenNumber: {
    fontSize: 52,
    fontWeight: '900',
    color: colors.primary,
    lineHeight: 60,
    marginVertical: 4,
    letterSpacing: -1,
  },
  tokenStatusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
    borderRadius: 20,
    marginTop: 4,
  },
  tokenStatusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  tokenStatusPillText: {
    fontSize: 12,
    fontWeight: '700',
  },
  queueStatsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.xs,
  },
  queueStatBox: {
    flex: 1,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  queueStatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 2,
  },
  queueStatTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  queueStatValue: {
    fontSize: 26,
    fontWeight: '900',
    color: colors.onSurface,
    marginTop: 2,
  },
  hospitalGuidanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerLowest,
    paddingHorizontal: spacing.sm,
    paddingVertical: 8,
    borderRadius: borderRadius.sm,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 6,
  },
  hospitalGuidanceText: {
    fontSize: 11,
    color: colors.textSecondary,
    flex: 1,
    lineHeight: 15,
  },
  // Consultation list
  consultationCard: {
    marginBottom: spacing.sm,
    padding: spacing.md,
  },
  consultationRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  consultationInfo: {
    flex: 1,
    marginHorizontal: spacing.sm,
  },
  consultationDate: {
    fontSize: 11,
    color: colors.textSecondary,
  },
  consultationComplaint: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.onSurface,
    marginTop: 2,
  },
});

export default HomeScreen;
