/**
 * Common Button Component
 * Matches the primary/secondary styling in the approved Clinova design.
 */
import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../../constants/theme';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost' | 'disabled';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  fullWidth?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  icon,
  fullWidth = false,
  style,
  textStyle,
}) => {
  const isEffectivelyDisabled = disabled || variant === 'disabled' || loading;

  const getContainerStyle = () => {
    switch (variant) {
      case 'secondary':
        return styles.secondaryContainer;
      case 'outline':
        return styles.outlineContainer;
      case 'danger':
        return styles.dangerContainer;
      case 'ghost':
        return styles.ghostContainer;
      case 'disabled':
        return styles.disabledContainer;
      case 'primary':
      default:
        return styles.primaryContainer;
    }
  };

  const getTextStyle = () => {
    switch (variant) {
      case 'secondary':
        return styles.secondaryText;
      case 'outline':
        return styles.outlineText;
      case 'danger':
        return styles.dangerText;
      case 'ghost':
        return styles.ghostText;
      case 'primary':
      default:
        return styles.primaryText;
    }
  };

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isEffectivelyDisabled}
      activeOpacity={0.85}
      style={[
        styles.baseContainer,
        getContainerStyle(),
        fullWidth && { width: '100%' },
        isEffectivelyDisabled && styles.disabledContainer,
        style,
      ]}
      accessibilityRole="button"
      accessibilityState={{ disabled: isEffectivelyDisabled }}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={variant === 'outline' || variant === 'ghost' ? colors.primary : colors.textLight}
        />
      ) : (
        <>
          <Text style={[styles.baseText, getTextStyle(), textStyle]}>
            {icon ? `${icon}  ${title}` : title}
          </Text>
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  baseContainer: {
    minHeight: 48,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  primaryContainer: {
    backgroundColor: colors.primary,
    shadowColor: colors.primaryDark,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 2,
  },
  secondaryContainer: {
    backgroundColor: colors.secondaryContainer,
  },
  outlineContainer: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: colors.primaryBorder,
  },
  dangerContainer: {
    backgroundColor: colors.error,
  },
  ghostContainer: {
    backgroundColor: 'transparent',
  },
  disabledContainer: {
    opacity: 0.5,
  },
  baseText: {
    ...typography.body.largeBold,
    textAlign: 'center',
  },
  primaryText: {
    color: colors.textLight,
  },
  secondaryText: {
    color: colors.onSecondaryContainer,
  },
  outlineText: {
    color: colors.primary,
  },
  dangerText: {
    color: colors.textLight,
  },
  ghostText: {
    color: colors.textSecondary,
  },
});
