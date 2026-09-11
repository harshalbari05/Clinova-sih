/**
 * LanguageSelectScreen
 *
 * Used when the patient starts "Talk to Clinova" from the dashboard.
 * consultationId is required in this context (interview is about to start).
 * Language is persisted so future sessions default to the same language.
 */
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
  const consultationId = route.params?.consultationId;

  const { language, setLanguage } = usePatient();
  const [selected, setSelected] = useState<string>(language || 'English');

  const handleContinue = async () => {
    await setLanguage(selected);

    if (consultationId) {
      // Interview flow — navigate directly to interview
      navigation.navigate('Interview', {
        consultationId,
        language: selected,
      });
    } else {
      // Should not happen in normal flow (consultationId always present here)
      navigation.goBack();
    }
  };

  return (
    <View style={styles.container}>
      <Header title="Interview Language" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.screenTitle}>भाषा चुनें / Choose Language</Text>
        <Text style={styles.screenSubtitle}>
          Select the language for your AI clinical interview. Clinova will ask
          you health questions in the chosen language.
        </Text>

        {LANGUAGES.map((item) => {
          const isSelected = selected === item.code;
          return (
            <TouchableOpacity
              key={item.code}
              activeOpacity={0.8}
              onPress={() => setSelected(item.code)}
              accessibilityRole="radio"
              accessibilityState={{ selected: isSelected }}
              accessibilityLabel={`${item.name} — ${item.nativeName}`}
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
          title="Start Interview / इंटरव्यू शुरू करें"
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
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: colors.textMuted,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
    flexShrink: 0,
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
    fontSize: 17,
    fontWeight: '700',
    color: colors.onSurface,
  },
  langNameSelected: {
    color: colors.primary,
  },
  langNativeName: {
    fontSize: 15,
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
    paddingVertical: spacing.md,
  },
});

export default LanguageSelectScreen;
