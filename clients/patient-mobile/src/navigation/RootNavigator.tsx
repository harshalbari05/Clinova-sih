import React from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { RootStackParamList } from './types';
import { usePatient } from '../context/PatientContext';
import colors from '../theme/colors';

// Pre-Auth & Consultation Screens
import {
  OnboardingLanguageScreen,
  ConsentScreen,
  HospitalSelectScreen,
  LanguageSelectScreen,
  InterviewScreen,
} from '../screens/Consultation';
import LoginScreen from '../screens/Auth/LoginScreen';
import RegisterScreen from '../screens/Auth/RegisterScreen';
import HomeScreen from '../screens/Dashboard/HomeScreen';
import DocumentUploadScreen from '../screens/Documents/DocumentUploadScreen';
import DocumentListScreen from '../screens/Documents/DocumentListScreen';
import DocumentExtractionScreen from '../screens/Documents/DocumentExtractionScreen';
import TimelineScreen from '../screens/Timeline/TimelineScreen';
import ClinicalSummaryScreen from '../screens/Summary/ClinicalSummaryScreen';
import { PatientQRScreen, ProfileScreen } from '../screens/Profile';

const Stack = createNativeStackNavigator<RootStackParamList>();

export const RootNavigator: React.FC = () => {
  const { isAuthenticated, isLoading, consentGiven } = usePatient();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.surface },
        animation: 'slide_from_right',
      }}
    >
      {!isAuthenticated ? (
        // Pre-Auth Stack: Language → Login / Register
        <Stack.Group>
          <Stack.Screen name="OnboardingLanguage" component={OnboardingLanguageScreen} />
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
        </Stack.Group>
      ) : !consentGiven ? (
        // Consent Gate: shown once after first login
        <Stack.Group>
          <Stack.Screen name="Consent" component={ConsentScreen} />
        </Stack.Group>
      ) : (
        // Authenticated & Consented — Full Patient Stack
        <Stack.Group>
          <Stack.Screen name="Home" component={HomeScreen} />
          <Stack.Screen name="HospitalSelect" component={HospitalSelectScreen} />
          <Stack.Screen name="LanguageSelect" component={LanguageSelectScreen} />
          <Stack.Screen name="Interview" component={InterviewScreen} />
          <Stack.Screen name="DocumentUpload" component={DocumentUploadScreen} />
          <Stack.Screen name="DocumentList" component={DocumentListScreen} />
          <Stack.Screen name="DocumentExtraction" component={DocumentExtractionScreen} />
          <Stack.Screen name="Timeline" component={TimelineScreen} />
          <Stack.Screen name="ClinicalSummary" component={ClinicalSummaryScreen} />
          <Stack.Screen name="PatientQR" component={PatientQRScreen} />
          <Stack.Screen name="Profile" component={ProfileScreen} />
        </Stack.Group>
      )}
    </Stack.Navigator>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
  },
});

export default RootNavigator;
