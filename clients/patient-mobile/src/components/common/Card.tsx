/**
 * Common Card Component
 * Styled to match cards in clinova_patient_dashboard and clinova_patient_medical_history
 */
import React, { ReactNode } from 'react';
import { View, StyleSheet, ViewStyle, TouchableOpacity } from 'react-native';
import { colors, borderRadius, spacing, shadows } from '../../constants/theme';

interface CardProps {
  children: ReactNode;
  style?: ViewStyle;
  onPress?: () => void;
  elevated?: boolean;
  highlighted?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  style,
  onPress,
  elevated = false,
  highlighted = false,
}) => {
  const cardStyles = [
    styles.card,
    elevated && styles.elevated,
    highlighted && styles.highlighted,
    style,
  ];

  if (onPress) {
    return (
      <TouchableOpacity
        onPress={onPress}
        activeOpacity={0.85}
        style={cardStyles}
        accessibilityRole="button"
      >
        {children}
      </TouchableOpacity>
    );
  }

  return <View style={cardStyles}>{children}</View>;
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.card,
  },
  elevated: {
    ...shadows.elevated,
  },
  highlighted: {
    borderColor: colors.primaryBorder,
    backgroundColor: '#FAFDFD',
  },
});
