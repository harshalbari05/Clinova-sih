import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { TriageResult } from '../types';
import colors from '../theme/colors';
import { borderRadius, spacing } from '../theme/spacing';

interface EmergencyBannerProps {
  triageResult: TriageResult;
  onDismiss?: () => void;
}

export const EmergencyBanner: React.FC<EmergencyBannerProps> = ({
  triageResult,
  onDismiss,
}) => {
  const isEmergency =
    triageResult.priority === 'red' ||
    triageResult.priority === 'EMERGENCY' ||
    triageResult.is_red_flag === true ||
    triageResult.requires_immediate_escalation === true;

  if (!isEmergency) return null;

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <View style={styles.iconTitleRow}>
          <Ionicons name="warning" size={24} color={colors.triageRed} />
          <Text style={styles.title}>EMERGENCY ALERT: SEEK IMMEDIATE CARE</Text>
        </View>
        {onDismiss && (
          <TouchableOpacity onPress={onDismiss} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
            <Ionicons name="close" size={20} color={colors.triageRed} />
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.bodyText}>
        Our clinical triage system detected symptoms that require urgent medical attention.
        Please go to the nearest Emergency Room or contact emergency medical services immediately.
      </Text>

      {triageResult.emergency_instructions ? (
        <View style={styles.instructionsContainer}>
          <Text style={styles.instructionsTitle}>Immediate Guidance:</Text>
          <Text style={styles.instructionsText}>{triageResult.emergency_instructions}</Text>
        </View>
      ) : null}

      {triageResult.red_flags_detected && triageResult.red_flags_detected.length > 0 && (
        <View style={styles.redFlagsContainer}>
          <Text style={styles.redFlagsTitle}>Triggering Indicators:</Text>
          {triageResult.red_flags_detected.map((flag, idx) => (
            <Text key={idx} style={styles.flagItem}>
              • {flag}
            </Text>
          ))}
        </View>
      )}

      <Text style={styles.disclaimer}>
        * This is an automated safety alert, NOT a clinical diagnosis or prescription. Do not delay emergency medical care.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.triageRedBg,
    borderColor: colors.triageRedBorder,
    borderWidth: 1.5,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginVertical: spacing.sm,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  iconTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.triageRed,
    marginLeft: spacing.xs + 2,
    flex: 1,
  },
  bodyText: {
    fontSize: 13,
    color: '#7F1D1D',
    lineHeight: 18,
    marginTop: spacing.xs,
  },
  instructionsContainer: {
    backgroundColor: '#FEE2E2',
    padding: spacing.sm,
    borderRadius: borderRadius.sm,
    marginTop: spacing.sm,
  },
  instructionsTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#991B1B',
  },
  instructionsText: {
    fontSize: 12,
    color: '#991B1B',
    marginTop: 2,
    lineHeight: 16,
  },
  redFlagsContainer: {
    marginTop: spacing.sm,
  },
  redFlagsTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#991B1B',
    marginBottom: 2,
  },
  flagItem: {
    fontSize: 12,
    color: '#991B1B',
    lineHeight: 16,
  },
  disclaimer: {
    fontSize: 10,
    color: '#991B1B',
    fontStyle: 'italic',
    marginTop: spacing.sm,
  },
});

export default EmergencyBanner;
