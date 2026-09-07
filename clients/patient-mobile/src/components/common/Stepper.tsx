/**
 * 7-Step Intake Stepper Component
 * Faithfully matches the stepper in clinova_patient_medical_history
 */
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { colors, typography, spacing, borderRadius } from '../../constants/theme';

export const STEP_TITLES = [
  'Basic Information',
  'Current Problem',
  'Symptoms',
  'Past Health Problems',
  'Medicines & Allergies',
  'Surgery & Family',
  'Review Summary',
];

interface StepperProps {
  currentStep: number;
  totalSteps?: number;
  onStepPress?: (step: number) => void;
}

export const Stepper: React.FC<StepperProps> = ({
  currentStep,
  totalSteps = 7,
  onStepPress,
}) => {
  const percentage = Math.round((currentStep / totalSteps) * 100);
  const currentTitle = STEP_TITLES[currentStep - 1] || 'Intake Step';

  return (
    <View style={styles.container}>
      {/* Step Header */}
      <View style={styles.headerRow}>
        <View style={styles.titleRow}>
          <Text style={styles.stepPrefix}>STEP </Text>
          <Text style={styles.stepCurrent}>{currentStep}</Text>
          <Text style={styles.stepTotal}> of {totalSteps}</Text>
          <Text style={styles.separator}>•</Text>
          <Text style={styles.titleText} numberOfLines={1}>
            {currentTitle}
          </Text>
        </View>
        <Text style={styles.percentageText}>{percentage}%</Text>
      </View>

      {/* Linear Progress Bar */}
      <View style={styles.progressBarBackground}>
        <View style={[styles.progressBarFill, { width: `${percentage}%` }]} />
      </View>

      {/* Step Number Pills */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.pillsRow}
      >
        {Array.from({ length: totalSteps }, (_, i) => i + 1).map((stepNum) => {
          const isActive = stepNum === currentStep;
          const isCompleted = stepNum < currentStep;

          return (
            <TouchableOpacity
              key={stepNum}
              onPress={() => onStepPress?.(stepNum)}
              style={[
                styles.pill,
                isActive && styles.activePill,
                isCompleted && styles.completedPill,
              ]}
              accessibilityRole="button"
              accessibilityLabel={`Go to step ${stepNum}`}
            >
              <Text
                style={[
                  styles.pillText,
                  isActive && styles.activePillText,
                  isCompleted && styles.completedPillText,
                ]}
              >
                {stepNum}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    paddingRight: spacing.sm,
  },
  stepPrefix: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textMuted,
    textTransform: 'uppercase',
  },
  stepCurrent: {
    fontSize: 15,
    fontWeight: '800',
    color: colors.primary,
  },
  stepTotal: {
    fontSize: 12,
    fontWeight: '500',
    color: colors.textMuted,
  },
  separator: {
    marginHorizontal: 6,
    color: colors.textSubtle,
  },
  titleText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.textPrimary,
    flexShrink: 1,
  },
  percentageText: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.primary,
  },
  progressBarBackground: {
    height: 6,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.full,
    overflow: 'hidden',
    marginBottom: spacing.sm,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: borderRadius.full,
  },
  pillsRow: {
    flexDirection: 'row',
    gap: spacing.xs + 2,
    paddingTop: 2,
  },
  pill: {
    width: 32,
    height: 32,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activePill: {
    backgroundColor: colors.primary,
  },
  completedPill: {
    backgroundColor: colors.primaryLight,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
  },
  pillText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textMuted,
  },
  activePillText: {
    color: colors.textLight,
  },
  completedPillText: {
    color: colors.primary,
  },
});
