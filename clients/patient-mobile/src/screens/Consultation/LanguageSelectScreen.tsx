import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp, ScreenRouteProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Button from '../../components/Button';
import StepIndicator from '../../components/StepIndicator';

interface LanguageOption {
  code: string;
  name: string;
  nativeName: string;
  description: string;
}

const LANGUAGES: LanguageOption[] = [
  {
    code: 'English',
    name: 'English',
    nativeName: 'English',
    description: 'Standard clinical questions in English',
  },
  {
    code: 'Hindi',
    name: 'Hindi',
    nativeName: 'हिन्दी',
    description: 'हिंदी में अपनी समस्याएं और लक्षण बताएं',
  },
  {
    code: 'Marathi',
    name: 'Marathi',
    nativeName: 'मराठी',
    description: 'मराठीत आपली लक्षणे आणि आरोग्य माहिती नोंदवा',
  },
];

export const LanguageSelectScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'LanguageSelect'>>();
  const route = useRoute<ScreenRouteProp<'LanguageSelect'>>();
  const { consultationId } = route.params;

  const { language, setLanguage } = usePatient();
  const [selected, setSelected] = useState<string>(language || 'English');

  const handleContinue = async () => {
    await setLanguage(selected);
    navigation.navigate('Interview', {
      consultationId,
      language: selected,
    });
  };

  return (
    <View style={styles.container}>
      <Header title="Choose Language" onBack={() => navigation.goBack()} />
      <StepIndicator currentStep={3} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.screenTitle}>Select Interview Language</Text>
        <Text style={styles.screenSubtitle}>
          Choose your preferred language for the AI-guided clinical intake questions and responses.
        </Text>

        {LANGUAGES.map((item) => {
          const isSelected = selected === item.code;
          return (
            <TouchableOpacity
              key={item.code}
              activeOpacity={0.8}
              onPress={() => setSelected(item.code)}
            >
              <Card
                style={[
                  styles.optionCard,
                  isSelected ? styles.optionCardSelected : null,
                ]}
              >
                <View style={styles.radioRow}>
                  <View style={[styles.radioCircle, isSelected && styles.radioCircleSelected]}>
                    {isSelected && <View style={styles.radioInner} />}
                  </View>
                  <View style={styles.langInfo}>
                    <View style={styles.langNameRow}>
                      <Text style={[styles.langName, isSelected && styles.langNameSelected]}>
                        {item.name}
                      </Text>
                      <Text style={styles.langNativeName}>({item.nativeName})</Text>
                    </View>
                    <Text style={styles.langDescription}>{item.description}</Text>
                  </View>
                  {isSelected && (
                    <Ionicons name="checkmark-circle" size={24} color={colors.primary} />
                  )}
                </View>
              </Card>
            </TouchableOpacity>
          );
        })}

        <Button
          title="Continue to AI Interview"
          onPress={handleContinue}
          style={styles.continueBtn}
        />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  scrollContent: {
    padding: spacing.md,
  },
  screenTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.onSurface,
    marginTop: spacing.sm,
  },
  screenSubtitle: {
    fontSize: 13,
    color: colors.textSecondary,
    marginTop: 4,
    marginBottom: spacing.lg,
    lineHeight: 18,
  },
  optionCard: {
    marginBottom: spacing.md,
    padding: spacing.md,
  },
  optionCardSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.surfaceContainerLow,
    borderWidth: 2,
  },
  radioRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  radioCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: colors.textMuted,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  radioCircleSelected: {
    borderColor: colors.primary,
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.primary,
  },
  langInfo: {
    flex: 1,
  },
  langNameRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  langName: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.onSurface,
  },
  langNameSelected: {
    color: colors.primary,
  },
  langNativeName: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textSecondary,
    marginLeft: 6,
  },
  langDescription: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  continueBtn: {
    marginTop: spacing.lg,
  },
});

export default LanguageSelectScreen;
