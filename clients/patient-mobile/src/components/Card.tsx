import React from 'react';
import { View, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import colors from '../theme/colors';
import { borderRadius, shadows, spacing } from '../theme/spacing';

interface CardProps {
  children: React.ReactNode;
  elevated?: boolean;
  style?: StyleProp<ViewStyle>;
}

export const Card: React.FC<CardProps> = ({ children, elevated = false, style }) => {
  return (
    <View style={[styles.card, elevated && styles.elevated, style]}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.cardBg,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    ...shadows.subtle,
  },
  elevated: {
    borderColor: colors.borderLight,
    ...shadows.card,
  },
});

export default Card;
