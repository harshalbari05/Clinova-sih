/**
 * OnboardingLanguageScreen
 *
 * First screen the patient sees when opening the app.
 * Lets them choose their preferred language before login.
 * Designed for elderly / rural / low-literacy users:
 *  - Very large touch targets (80px height)
 *  - Large native-language labels
 *  - Minimal text
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import colors from '../../theme/colors';
import { borderRadius, spacing, shadows } from '../../theme/spacing';

interface LangOption {
  code: string;
  label: string;
  native: string;
  flag: string;
}

const LANGUAGES: LangOption[] = [
  { code: 'English', label: 'English', native: 'English', flag: '🇬🇧' },
  { code: 'Hindi', label: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
  { code: 'Marathi', label: 'Marathi', native: 'मराठी', flag: '🇮🇳' },
];

export const OnboardingLanguageScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'OnboardingLanguage'>>();
  const { setLanguage, language } = usePatient();
  const [selected, setSelected] = useState<string>(language || 'English');

  const handleContinue = async () => {
    await setLanguage(selected);
    navigation.navigate('Login');
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.surface} />
      <View style={styles.container}>
        {/* Branding */}
        <View style={styles.brandRow}>
          <View style={styles.brandBadge}>
            <Text style={styles.brandBadgeText}>+</Text>
          </View>
          <Text style={styles.brandName}>Clinova</Text>
        </View>

        <Text style={styles.heading}>अपनी भाषा चुनें</Text>
        <Text style={styles.subheading}>Choose Your Language / आपली भाषा निवडा</Text>

        {/* Large language option buttons */}
        <View style={styles.optionList}>
          {LANGUAGES.map((lang) => {
            const isSelected = selected === lang.code;
            return (
              <TouchableOpacity
                key={lang.code}
                style={[styles.optionBtn, isSelected && styles.optionBtnSelected]}
                activeOpacity={0.75}
                onPress={() => setSelected(lang.code)}
                accessibilityRole="radio"
                accessibilityState={{ selected: isSelected }}
                accessibilityLabel={`${lang.label} — ${lang.native}`}
              >
                <Text style={styles.optionFlag}>{lang.flag}</Text>
                <View style={styles.optionTextCol}>
                  <Text style={[styles.optionNative, isSelected && styles.optionNativeSelected]}>
                    {lang.native}
                  </Text>
                  {lang.native !== lang.label && (
                    <Text style={styles.optionLabel}>{lang.label}</Text>
                  )}
                </View>
                <View style={[styles.radioOuter, isSelected && styles.radioOuterSelected]}>
                  {isSelected && <View style={styles.radioInner} />}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Continue Button */}
        <TouchableOpacity
          style={styles.continueBtn}
          activeOpacity={0.85}
          onPress={handleContinue}
          accessibilityRole="button"
          accessibilityLabel="Continue to Login"
        >
          <Text style={styles.continueBtnText}>आगे बढ़ें / Continue</Text>
          <Ionicons name="arrow-forward" size={22} color={colors.onPrimary} style={{ marginLeft: 8 }} />
        </TouchableOpacity>

        <Text style={styles.footerNote}>Clinova • AI-Powered Patient Health Platform</Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  container: {
    flex: 1,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl,
    paddingBottom: spacing.xl,
    justifyContent: 'center',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xl,
  },
  brandBadge: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
    ...shadows.subtle,
  },
  brandBadgeText: {
    color: colors.onPrimary,
    fontSize: 30,
    fontWeight: '700',
    lineHeight: 34,
  },
  brandName: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.primary,
    letterSpacing: -0.5,
  },
  heading: {
    fontSize: 26,
    fontWeight: '700',
    color: colors.onSurface,
    textAlign: 'center',
    marginBottom: 6,
  },
  subheading: {
    fontSize: 15,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.xl,
    lineHeight: 22,
  },
  optionList: {
    gap: spacing.md,
    marginBottom: spacing.xl,
  },
  optionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: 20,
    borderRadius: borderRadius.lg,
    borderWidth: 2,
    borderColor: colors.border,
    backgroundColor: colors.cardBg,
    ...shadows.subtle,
  },
  optionBtnSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.surfaceContainerLow,
  },
  optionFlag: {
    fontSize: 32,
    marginRight: spacing.md,
  },
  optionTextCol: {
    flex: 1,
  },
  optionNative: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.onSurface,
  },
  optionNativeSelected: {
    color: colors.primary,
  },
  optionLabel: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: 2,
  },
  radioOuter: {
    width: 26,
    height: 26,
    borderRadius: 13,
    borderWidth: 2,
    borderColor: colors.textMuted,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioOuterSelected: {
    borderColor: colors.primary,
  },
  radioInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.primary,
  },
  continueBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    paddingVertical: 18,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.lg,
    ...shadows.subtle,
  },
  continueBtnText: {
    color: colors.onPrimary,
    fontSize: 18,
    fontWeight: '700',
  },
  footerNote: {
    textAlign: 'center',
    fontSize: 12,
    color: colors.textMuted,
  },
});

export default OnboardingLanguageScreen;
