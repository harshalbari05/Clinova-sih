/**
 * PatientQRScreen
 *
 * Displays a QR code representing the patient's Clinova registration.
 * QR encodes: CLINOVA:PATIENT:{patient.id}
 *
 * SAFE: Contains ONLY the patient registration identifier — NO clinical data,
 * NO medical history, NO medications, NO reports.
 *
 * Hospital reception scans this QR to pull up the patient's profile during visit.
 * Uses a public QR image generation API (no new package needed).
 */
import React, { useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  ActivityIndicator,
  TouchableOpacity,
  Share,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import colors from '../../theme/colors';
import { borderRadius, shadows, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';

export const PatientQRScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'PatientQR'>>();
  const { patient, user } = usePatient();

  const patientId = patient?.id || user?.id || '';
  const displayName = patient?.full_name || 'Patient';
  const displayId = patientId ? patientId.substring(0, 8).toUpperCase() : '—';
  const abhaId = patient?.abha_id;

  // QR payload — safe identifier only, no clinical data
  const qrPayload = `CLINOVA:PATIENT:${patientId}`;

  // Use public QR generation API — no extra package required
  const qrImageUrl = useMemo(() => {
    if (!patientId) return null;
    const encoded = encodeURIComponent(qrPayload);
    return `https://api.qrserver.com/v1/create-qr-code/?size=280x280&margin=16&data=${encoded}`;
  }, [qrPayload, patientId]);

  const handleShare = async () => {
    try {
      await Share.share({
        message: `My Clinova Patient ID: ${displayId}\nFull ID: ${patientId}`,
        title: 'Clinova Patient QR',
      });
    } catch {
      // Ignore share errors
    }
  };

  return (
    <View style={styles.container}>
      <Header title="मेरा QR कोड / My QR Code" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* QR Card */}
        <Card elevated style={styles.qrCard}>
          {/* Patient Identity */}
          <View style={styles.identityRow}>
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarText}>
                {displayName.charAt(0).toUpperCase()}
              </Text>
            </View>
            <View style={styles.identityInfo}>
              <Text style={styles.patientName}>{displayName}</Text>
              <Text style={styles.patientIdLabel}>
                Clinova ID: <Text style={styles.patientIdValue}>{displayId}...</Text>
              </Text>
              {abhaId && (
                <View style={styles.abhaBadge}>
                  <Ionicons name="card-outline" size={12} color={colors.primary} />
                  <Text style={styles.abhaText}>ABHA: {abhaId}</Text>
                </View>
              )}
            </View>
          </View>

          {/* QR Code */}
          <View style={styles.qrContainer}>
            {!patientId ? (
              <View style={styles.qrPlaceholder}>
                <Ionicons name="alert-circle-outline" size={40} color={colors.textMuted} />
                <Text style={styles.qrPlaceholderText}>Patient ID not available</Text>
              </View>
            ) : qrImageUrl ? (
              <Image
                source={{ uri: qrImageUrl }}
                style={styles.qrImage}
                resizeMode="contain"
                onLoadStart={() => {}}
                onError={() => {}}
                accessibilityLabel={`QR code for patient ${displayName}`}
              />
            ) : (
              <ActivityIndicator size="large" color={colors.primary} />
            )}
          </View>

          <Text style={styles.qrLabel}>
            अस्पताल रिसेप्शन पर यह QR स्कैन करें
          </Text>
          <Text style={styles.qrLabelEn}>
            Show this QR at hospital reception for registration
          </Text>
        </Card>

        {/* Info Card */}
        <Card style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Ionicons name="shield-checkmark-outline" size={20} color={colors.primary} />
            <Text style={styles.infoText}>
              This QR contains <Text style={{ fontWeight: '700' }}>only your registration ID</Text>.
              No medical records or clinical data is stored in this code.
            </Text>
          </View>
          <View style={[styles.infoRow, { marginTop: spacing.sm }]}>
            <Ionicons name="information-circle-outline" size={20} color={colors.textSecondary} />
            <Text style={styles.infoText}>
              Hospital staff will scan this during your visit to access your Clinova health summary.
            </Text>
          </View>
        </Card>

        {/* Share Button */}
        <TouchableOpacity
          style={styles.shareBtn}
          activeOpacity={0.8}
          onPress={handleShare}
          accessibilityRole="button"
          accessibilityLabel="Share my Patient ID"
        >
          <Ionicons name="share-outline" size={20} color={colors.primary} />
          <Text style={styles.shareBtnText}>Share Patient ID</Text>
        </TouchableOpacity>
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
    paddingBottom: 40,
  },
  qrCard: {
    padding: spacing.lg,
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  identityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'stretch',
    marginBottom: spacing.lg,
  },
  avatarCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
    flexShrink: 0,
  },
  avatarText: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.onPrimary,
  },
  identityInfo: {
    flex: 1,
  },
  patientName: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.onSurface,
  },
  patientIdLabel: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 2,
  },
  patientIdValue: {
    fontWeight: '700',
    color: colors.primary,
    fontFamily: 'monospace' as any,
  },
  abhaBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainer,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: borderRadius.sm,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  abhaText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.primary,
    marginLeft: 4,
  },
  qrContainer: {
    width: 280,
    height: 280,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: '#FFFFFF',
    marginBottom: spacing.md,
    ...shadows.subtle,
  },
  qrImage: {
    width: 280,
    height: 280,
    borderRadius: borderRadius.lg,
  },
  qrPlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  qrPlaceholderText: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
  qrLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.onSurface,
    textAlign: 'center',
  },
  qrLabelEn: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 4,
  },
  infoCard: {
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  infoText: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
    flex: 1,
    marginLeft: spacing.sm,
    lineHeight: 18,
  },
  shareBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingVertical: 14,
    marginBottom: spacing.md,
  },
  shareBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.primary,
    marginLeft: spacing.sm,
  },
});

export default PatientQRScreen;
