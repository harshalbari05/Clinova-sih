import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import colors from '../theme/colors';
import { borderRadius, spacing } from '../theme/spacing';

export type BadgeVariant =
  | 'verified'
  | 'unverified'
  | 'clinician'
  | 'red'
  | 'orange'
  | 'yellow'
  | 'green'
  | 'neutral';

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  style?: ViewStyle;
}

export const Badge: React.FC<BadgeProps> = ({ label, variant = 'neutral', style }) => {
  const getColors = () => {
    switch (variant) {
      case 'verified':
        return { bg: colors.verifiedBg, text: colors.verified };
      case 'unverified':
        return { bg: colors.unverifiedBg, text: colors.unverified };
      case 'clinician':
        return { bg: colors.clinicianVerifiedBg, text: colors.clinicianVerified };
      case 'red':
        return { bg: colors.triageRedBg, text: colors.triageRed };
      case 'orange':
        return { bg: colors.triageOrangeBg, text: colors.triageOrange };
      case 'yellow':
        return { bg: colors.triageYellowBg, text: colors.triageYellow };
      case 'green':
        return { bg: colors.triageGreenBg, text: colors.triageGreen };
      case 'neutral':
      default:
        return { bg: colors.surfaceContainer, text: colors.textSecondary };
    }
  };

  const { bg, text } = getColors();

  return (
    <View style={[styles.badge, { backgroundColor: bg }, style]}>
      <Text style={[styles.text, { color: text }]}>{label}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
});

export default Badge;
