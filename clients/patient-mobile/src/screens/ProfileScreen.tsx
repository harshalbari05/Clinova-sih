import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Modal,
} from 'react-native';
import { colors, spacing, borderRadius, typography, shadows } from '../constants/theme';
import { Header } from '../components/common/Header';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { useAuth } from '../context/AuthContext';
import { useConsultation } from '../context/ConsultationContext';
import { getApiBaseUrl, setApiBaseUrl } from '../config/env';

interface ProfileScreenProps {
  navigation?: any;
  onNavigateToHome?: () => void;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({
  navigation,
  onNavigateToHome,
}) => {
  const { user, patient, logout } = useAuth();
  const { language, setLanguage } = useConsultation();

  const [apiModalVisible, setApiModalVisible] = useState(false);
  const [customApiUrl, setCustomApiUrl] = useState(getApiBaseUrl());
  const [currentBaseUrl, setCurrentBaseUrl] = useState(getApiBaseUrl());

  const handleSaveApiUrl = () => {
    if (!customApiUrl.trim()) {
      Alert.alert('Invalid URL', 'API base URL cannot be empty.');
      return;
    }
    setApiBaseUrl(customApiUrl.trim());
    setCurrentBaseUrl(getApiBaseUrl());
    setApiModalVisible(false);
    Alert.alert(
      'API URL Updated',
      `Central API base URL is now set to:\n${getApiBaseUrl()}`
    );
  };

  const handleResetApiUrl = () => {
    // Reset to default
    const defaultUrl = 'http://10.0.2.2:8000/api/v1';
    setApiBaseUrl(defaultUrl);
    setCustomApiUrl(defaultUrl);
    setCurrentBaseUrl(defaultUrl);
    setApiModalVisible(false);
    Alert.alert('Reset to Default', `API base URL reset to:\n${defaultUrl}`);
  };

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out of Clinova?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: async () => {
          await logout();
        },
      },
    ]);
  };

  return (
    <View style={styles.container}>
      <Header
        title="CLINOVA"
        subtitle="Patient Profile"
        showBack={false}
      />

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* User Identity Header Card */}
        <View style={styles.profileHeaderCard}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarEmoji}>👤</Text>
          </View>
          <View style={styles.profileMeta}>
            <Text style={styles.profileName}>{patient?.full_name || 'Rahul Sharma'}</Text>
            <Text style={styles.profilePhone}>{patient?.phone || '+91 98765 43210'}</Text>
            <Text style={styles.profileEmail}>{user?.email || 'patient@clinova.health'}</Text>
          </View>
          <View style={styles.patientIdBadge}>
            <Text style={styles.patientIdText}>
              ID: {patient?.id ? patient.id.slice(0, 8).toUpperCase() : 'CLN-8831'}
            </Text>
          </View>
        </View>

        {/* ABHA / Ayushman Bharat Digital Health Account */}
        <View style={styles.section}>
          <View style={styles.sectionHeaderRow}>
            <Text style={styles.sectionTitle}>Digital Health Identity</Text>
          </View>

          <View style={styles.abhaCard}>
            <View style={styles.abhaTopRow}>
              <View style={styles.abhaBadge}>
                <Text style={styles.abhaBadgeText}>ABHA</Text>
              </View>
              <View style={styles.abhaConnectedPill}>
                <View style={styles.connectedDot} />
                <Text style={styles.connectedText}>Connected</Text>
              </View>
            </View>

            <Text style={styles.abhaTitle}>Ayushman Bharat Health Account</Text>
            <Text style={styles.abhaNumber}>
              {patient?.abha_id || '91-4521-8890-1234'}
            </Text>
            <Text style={styles.abhaFootnote}>
              Linked to your Clinova patient profile for identity and hospital check-in association.
            </Text>
          </View>
        </View>

        {/* Clinical Demographics Card */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Basic Health Details</Text>
          <View style={styles.demographicsCard}>
            <View style={styles.demoItem}>
              <Text style={styles.demoLabel}>Biological Sex</Text>
              <Text style={styles.demoValue}>{patient?.gender || 'Male'}</Text>
            </View>
            <View style={styles.demoItem}>
              <Text style={styles.demoLabel}>Date of Birth / Age</Text>
              <Text style={styles.demoValue}>
                {patient?.date_of_birth || patient?.dob || '14 May 1990 (34 Yrs)'}
              </Text>
            </View>
            <View style={styles.demoItem}>
              <Text style={styles.demoLabel}>Blood Group</Text>
              <Text style={styles.demoValue}>{patient?.blood_group || 'O+'}</Text>
            </View>
            <View style={styles.demoItem}>
              <Text style={styles.demoLabel}>Emergency Contact</Text>
              <Text style={styles.demoValue}>{patient?.emergency_contact || '+91 98111 22334'}</Text>
            </View>
          </View>
        </View>

        {/* Language Selection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Language Preference</Text>
          <Text style={styles.sectionSubtitle}>
            AI clinical interview and consultation guidance language
          </Text>

          <View style={styles.langGrid}>
            {[
              { code: 'en', label: 'English', sub: 'Default' },
              { code: 'hi', label: 'हिंदी (Hindi)', sub: 'North Region' },
              { code: 'mr', label: 'मराठी (Marathi)', sub: 'Maharashtra' },
            ].map((lang) => {
              const active = language === lang.code;
              return (
                <TouchableOpacity
                  key={lang.code}
                  style={[styles.langCard, active && styles.langCardActive]}
                  onPress={() => setLanguage(lang.code as any)}
                >
                  <View style={styles.langRadioCircle}>
                    {active && <View style={styles.langRadioDot} />}
                  </View>
                  <View style={styles.langMeta}>
                    <Text style={[styles.langLabel, active && styles.langLabelActive]}>
                      {lang.label}
                    </Text>
                    <Text style={styles.langSub}>{lang.sub}</Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* AYUSH Integration (Phase 2 / Disabled Notice) */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Holistic &amp; AYUSH Profiling</Text>
          <View style={styles.ayushCardDisabled}>
            <View style={styles.ayushHeaderRow}>
              <View style={styles.ayushBadge}>
                <Text style={styles.ayushBadgeText}>🌿 AYUSH</Text>
              </View>
              <Badge text="Phase 2 / Future" variant="neutral" size="small" />
            </View>
            <Text style={styles.ayushTitle}>Ayurvedic &amp; Traditional Intake</Text>
            <Text style={styles.ayushNotice}>
              Prakriti, Dosha analysis, and Ayurvedic consultation workflows are scheduled for Phase 2.
              No clinical AYUSH logic is active in this release.
            </Text>
          </View>
        </View>

        {/* Developer / LAN Network Connection Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Network &amp; Backend Server</Text>
          <View style={styles.networkCard}>
            <View style={styles.networkInfoRow}>
              <View>
                <Text style={styles.networkLabel}>API Base URL</Text>
                <Text style={styles.networkUrl} numberOfLines={1}>
                  {currentBaseUrl}
                </Text>
              </View>
              <TouchableOpacity
                style={styles.editNetworkBtn}
                onPress={() => setApiModalVisible(true)}
              >
                <Text style={styles.editNetworkBtnText}>Configure</Text>
              </TouchableOpacity>
            </View>
            <Text style={styles.networkHint}>
              Physical Android phone testing requires your computer's LAN IP address (e.g.{' '}
              <Text style={{ fontFamily: 'monospace' }}>http://192.168.x.x:8000/api/v1</Text>).
            </Text>
          </View>
        </View>

        {/* Logout Button */}
        <View style={[styles.section, { marginTop: spacing.xl, marginBottom: spacing.xxl }]}>
          <Button
            title="Sign Out of Clinova"
            onPress={handleLogout}
            variant="danger"
            icon="🚪"
            fullWidth
          />
          <Text style={styles.versionText}>Clinova Mobile v1.0.0 • SIH 2026 Edition</Text>
        </View>
      </ScrollView>

      {/* Network Configuration Modal */}
      <Modal
        visible={apiModalVisible}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setApiModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalHeading}>Configure Backend URL</Text>
            <Text style={styles.modalDesc}>
              Enter the network address where the Clinova FastAPI backend is running.
            </Text>

            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>API URL:</Text>
              <TextInput
                style={styles.modalInput}
                value={customApiUrl}
                onChangeText={setCustomApiUrl}
                placeholder="http://192.168.1.100:8000/api/v1"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View style={styles.modalPresets}>
              <Text style={styles.presetTitle}>Quick Presets:</Text>
              <TouchableOpacity
                style={styles.presetBtn}
                onPress={() => setCustomApiUrl('http://10.0.2.2:8000/api/v1')}
              >
                <Text style={styles.presetText}>Android Emulator (10.0.2.2:8000)</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.presetBtn}
                onPress={() => setCustomApiUrl('http://localhost:8000/api/v1')}
              >
                <Text style={styles.presetText}>Localhost (localhost:8000)</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalButtonsRow}>
              <TouchableOpacity
                style={styles.modalCancelBtn}
                onPress={() => setApiModalVisible(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalResetBtn}
                onPress={handleResetApiUrl}
              >
                <Text style={styles.modalResetText}>Reset</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.modalSaveBtn}
                onPress={handleSaveApiUrl}
              >
                <Text style={styles.modalSaveText}>Save</Text>
              </TouchableOpacity>
            </View>
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
  profileHeaderCard: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.md,
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.outlineVariant,
    ...shadows.sm,
    position: 'relative',
  },
  avatarCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.secondaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  avatarEmoji: {
    fontSize: 28,
  },
  profileMeta: {
    flex: 1,
  },
  profileName: {
    ...typography.headlineSm,
    color: colors.onSurface,
    fontWeight: '700',
  },
  profilePhone: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginTop: 2,
  },
  profileEmail: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginTop: 2,
  },
  patientIdBadge: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    backgroundColor: colors.surfaceContainerLow,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.md,
  },
  patientIdText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.primary,
    fontFamily: 'monospace',
  },
  section: {
    paddingHorizontal: spacing.lg,
    marginTop: spacing.lg,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  sectionTitle: {
    ...typography.bodyBold,
    color: colors.onSurface,
    marginBottom: spacing.xs,
  },
  sectionSubtitle: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginBottom: spacing.sm,
  },
  abhaCard: {
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
    ...shadows.sm,
  },
  abhaTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  abhaBadge: {
    backgroundColor: colors.surfaceContainerLow,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  abhaBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.primary,
    letterSpacing: 0.5,
  },
  abhaConnectedPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.secondaryContainer,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
  },
  connectedDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.secondary,
    marginRight: 4,
  },
  connectedText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.onSecondaryContainer,
  },
  abhaTitle: {
    ...typography.labelMd,
    color: colors.onSurface,
    fontWeight: '700',
  },
  abhaNumber: {
    fontFamily: 'monospace',
    fontSize: 15,
    fontWeight: '700',
    color: colors.primary,
    marginTop: 4,
  },
  abhaFootnote: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginTop: spacing.xs,
    lineHeight: 16,
  },
  demographicsCard: {
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  demoItem: {
    width: '50%',
    marginBottom: spacing.sm,
  },
  demoLabel: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
  },
  demoValue: {
    ...typography.bodyBold,
    color: colors.onSurface,
    marginTop: 2,
  },
  langGrid: {
    gap: spacing.sm,
  },
  langCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  langCardActive: {
    borderColor: colors.primary,
    backgroundColor: colors.surfaceContainerLow,
  },
  langRadioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: colors.outlineVariant,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  langRadioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.primary,
  },
  langMeta: {
    flex: 1,
  },
  langLabel: {
    ...typography.bodyBold,
    color: colors.onSurface,
  },
  langLabelActive: {
    color: colors.primary,
  },
  langSub: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    marginTop: 2,
  },
  ayushCardDisabled: {
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
    opacity: 0.85,
  },
  ayushHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  ayushBadge: {
    backgroundColor: colors.surfaceContainerLowest,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.md,
  },
  ayushBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.onSurface,
  },
  ayushTitle: {
    ...typography.bodyBold,
    color: colors.onSurface,
    marginTop: spacing.xs,
  },
  ayushNotice: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    lineHeight: 16,
    marginTop: spacing.xs,
  },
  networkCard: {
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xl,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  networkInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  networkLabel: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    fontWeight: '700',
  },
  networkUrl: {
    fontFamily: 'monospace',
    fontSize: 12,
    color: colors.primary,
    marginTop: 2,
    maxWidth: 200,
  },
  editNetworkBtn: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surfaceContainerLow,
  },
  editNetworkBtnText: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '700',
  },
  networkHint: {
    fontSize: 11,
    color: colors.onSurfaceVariant,
    lineHeight: 16,
  },
  versionText: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    textAlign: 'center',
    marginTop: spacing.md,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  modalCard: {
    width: '100%',
    backgroundColor: colors.surfaceContainerLowest,
    borderRadius: borderRadius.xxl,
    padding: spacing.lg,
    gap: spacing.md,
    ...shadows.lg,
  },
  modalHeading: {
    ...typography.headlineSm,
    color: colors.onSurface,
    fontWeight: '700',
  },
  modalDesc: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    lineHeight: 16,
  },
  inputContainer: {
    gap: spacing.xs,
  },
  inputLabel: {
    ...typography.labelMd,
    color: colors.onSurface,
    fontWeight: '700',
  },
  modalInput: {
    minHeight: 46,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.md,
    fontFamily: 'monospace',
    fontSize: 13,
    color: colors.onSurface,
  },
  modalPresets: {
    gap: spacing.xs,
  },
  presetTitle: {
    ...typography.caption,
    color: colors.onSurfaceVariant,
    fontWeight: '700',
  },
  presetBtn: {
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.sm,
    borderRadius: borderRadius.md,
  },
  presetText: {
    ...typography.caption,
    color: colors.primary,
    fontFamily: 'monospace',
  },
  modalButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  modalCancelBtn: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  modalCancelText: {
    ...typography.labelMd,
    color: colors.onSurfaceVariant,
  },
  modalResetBtn: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.md,
  },
  modalResetText: {
    ...typography.labelMd,
    color: colors.onSurface,
  },
  modalSaveBtn: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
  },
  modalSaveText: {
    ...typography.labelMd,
    color: colors.onPrimary,
    fontWeight: '700',
  },
});
