/**
 * Common Top App Header
 * Faithfully matches header in clinova_patient_dashboard and clinova_patient_staff_login
 */
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { colors, typography, spacing, borderRadius } from '../../constants/theme';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  showBack?: boolean;
  onBack?: () => void;
  onBackPress?: () => void;
  hospitalToken?: string;
  rightAction?: {
    label: string;
    onPress: () => void;
    icon?: string;
  };
  patientInitials?: string;
  onProfilePress?: () => void;
  onNotificationPress?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title = 'CLINOVA',
  subtitle = 'Patient Portal',
  showBack = false,
  onBack,
  onBackPress,
  hospitalToken,
  rightAction,
  patientInitials = 'RS',
  onProfilePress,
  onNotificationPress,
}) => {
  const handleBack = onBackPress || onBack;

  return (
    <View style={styles.container}>
      <View style={styles.leftRow}>
        {showBack && (
          <TouchableOpacity
            onPress={handleBack}
            style={styles.iconButton}
            accessibilityRole="button"
            accessibilityLabel="Go back"
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
        )}

        {/* Logo Badge */}
        <View style={styles.logoBadge}>
          <Text style={styles.logoIcon}>🏥</Text>
        </View>

        <View style={styles.titleColumn}>
          <Text style={styles.brandTitle}>{title}</Text>
          <Text style={styles.brandSubtitle}>{subtitle}</Text>
        </View>
      </View>

      <View style={styles.rightRow}>
        {rightAction ? (
          <TouchableOpacity
            onPress={rightAction.onPress}
            style={styles.actionPill}
            accessibilityRole="button"
          >
            <Text style={styles.actionPillText}>{rightAction.label}</Text>
          </TouchableOpacity>
        ) : (
          <>
            {onNotificationPress && (
              <TouchableOpacity
                onPress={onNotificationPress}
                style={styles.bellButton}
                accessibilityRole="button"
                accessibilityLabel="Notifications"
              >
                <Text style={styles.bellIcon}>🔔</Text>
                <View style={styles.notificationDot} />
              </TouchableOpacity>
            )}

            {onProfilePress && (
              <TouchableOpacity
                onPress={onProfilePress}
                style={styles.profilePill}
                accessibilityRole="button"
                accessibilityLabel="Profile menu"
              >
                <View style={styles.avatarCircle}>
                  <Text style={styles.avatarText}>{patientInitials}</Text>
                </View>
                <Text style={styles.profileArrow}>▾</Text>
              </TouchableOpacity>
            )}
          </>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  leftRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  iconButton: {
    width: 36,
    height: 36,
    borderRadius: borderRadius.full,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceContainerLow,
    marginRight: 2,
  },
  backArrow: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  logoBadge: {
    width: 34,
    height: 34,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primaryLight,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoIcon: {
    fontSize: 18,
  },
  titleColumn: {
    flexDirection: 'column',
  },
  brandTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: colors.textPrimary,
    letterSpacing: -0.3,
  },
  brandSubtitle: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  rightRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  bellButton: {
    width: 36,
    height: 36,
    borderRadius: borderRadius.full,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceContainerLow,
    position: 'relative',
  },
  bellIcon: {
    fontSize: 15,
  },
  notificationDot: {
    position: 'absolute',
    top: 6,
    right: 6,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.emerald,
    borderWidth: 1.5,
    borderColor: colors.surface,
  },
  profilePill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.full,
    paddingRight: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  avatarCircle: {
    width: 28,
    height: 28,
    borderRadius: borderRadius.full,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.textLight,
    fontSize: 11,
    fontWeight: '700',
  },
  profileArrow: {
    fontSize: 11,
    marginLeft: 4,
    color: colors.textMuted,
  },
  actionPill: {
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primaryLight,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
  },
  actionPillText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primary,
  },
});
