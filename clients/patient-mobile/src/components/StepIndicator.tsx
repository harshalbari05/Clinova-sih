import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import colors from '../theme/colors';
import { spacing } from '../theme/spacing';

interface StepIndicatorProps {
  currentStep: number; // 1 to 6
  totalSteps?: number;
}

const STEP_LABELS = ['Hospital', 'Consent', 'Language', 'Interview', 'Docs', 'Summary'];

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  currentStep,
  totalSteps = 6,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.stepsRow}>
        {Array.from({ length: totalSteps }).map((_, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;

          return (
            <React.Fragment key={index}>
              {index > 0 && (
                <View
                  style={[
                    styles.connector,
                    isCompleted && styles.connectorActive,
                  ]}
                />
              )}
              <View
                style={[
                  styles.circle,
                  isCurrent && styles.circleCurrent,
                  isCompleted && styles.circleCompleted,
                ]}
              >
                <Text
                  style={[
                    styles.stepNumber,
                    (isCurrent || isCompleted) && styles.stepNumberActive,
                  ]}
                >
                  {isCompleted ? '✓' : stepNumber}
                </Text>
              </View>
            </React.Fragment>
          );
        })}
      </View>
      <Text style={styles.label}>
        Step {currentStep} of {totalSteps}: {STEP_LABELS[currentStep - 1] || ''}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.surface,
    alignItems: 'center',
  },
  stepsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    maxWidth: 320,
  },
  connector: {
    flex: 1,
    height: 2,
    backgroundColor: colors.border,
  },
  connectorActive: {
    backgroundColor: colors.primary,
  },
  circle: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: colors.surfaceContainer,
    borderWidth: 1.5,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  circleCurrent: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  circleCompleted: {
    borderColor: colors.primary,
    backgroundColor: colors.primary,
  },
  stepNumber: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  stepNumberActive: {
    color: colors.onPrimary,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.onSurfaceVariant,
    marginTop: spacing.xs,
  },
});

export default StepIndicator;
