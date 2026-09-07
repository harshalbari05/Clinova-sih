/**
 * Status Badge Component
 * Formats statuses such as Complete, Incomplete, Verified, Needs Review, Priority, Emergency
 */
import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { colors, borderRadius, spacing } from '../../constants/theme';

export type BadgeType =
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'neutral'
  | 'priority';

interface BadgeProps {
  label?: string;
  text?: string;
  type?: BadgeType;
  variant?: BadgeType | 'danger' | string;
  size?: 'small' | 'medium' | 'large';
  dot?: boolean;
  style?: ViewStyle;
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  text,
  type,
  variant,
  size = 'medium',
  dot = false,
  style,
}) => {
  const displayText = label || text || '';
  const resolvedType: BadgeType = (type || (variant === 'danger' ? 'error' : variant) || 'info') as BadgeType;

  const getContainerStyle = () => {
    switch (resolvedType) {
      case 'success':
        return styles.successBg;
      case 'warning':
        return styles.warningBg;
      case 'error':
        return styles.errorBg;
      case 'priority':
        return styles.priorityBg;
      case 'neutral':
        return styles.neutralBg;
      case 'info':
      default:
        return styles.infoBg;
    }
  };

  const getTextColor = () => {
    switch (resolvedType) {
      case 'success':
        return colors.emerald;
      case 'warning':
        return colors.onWarningContainer;
      case 'error':
        return colors.error;
      case 'priority':
        return colors.primary;
      case 'neutral':
        return colors.textMuted;
      case 'info':
      default:
        return colors.primary;
    }
  };

  return (
    <View style={[styles.badge, getContainerStyle(), style]}>
      {dot && <View style={[styles.dot, { backgroundColor: getTextColor() }]} />}
      <Text style={[styles.label, { color: getTextColor() }]}>{displayText}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 3,
    borderRadius: borderRadius.full,
    alignSelf: 'flex-start',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 5,
  },
  label: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  successBg: {
    backgroundColor: colors.emeraldLight,
    borderWidth: 1,
    borderColor: colors.emeraldBorder,
  },
  warningBg: {
    backgroundColor: colors.warningContainer,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  errorBg: {
    backgroundColor: colors.errorContainer,
    borderWidth: 1,
    borderColor: '#FECDD3',
  },
  priorityBg: {
    backgroundColor: colors.primaryLight,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
  },
  neutralBg: {
    backgroundColor: colors.surfaceContainerLow,
    borderWidth: 1,
    borderColor: colors.border,
  },
  infoBg: {
    backgroundColor: colors.infoContainer,
    borderWidth: 1,
    borderColor: '#BAE6FD',
  },
});
