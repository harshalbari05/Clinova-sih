import React from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { RootStackParamList } from './types';
import { usePatient } from '../context/PatientContext';
import colors from '../theme/colors';

// Auth Screens
import LoginScreen from '../screens/Auth/LoginScreen';
import RegisterScreen from '../screens/Auth/RegisterScreen';

// Main Intake & Dashboard Screens
import HomeScreen from '../screens/Dashboard/HomeScreen';
import HospitalSelectScreen from '../screens/Consultation/HospitalSelectScreen';
import ConsentScreen from '../screens/Consultation/ConsentScreen';
import LanguageSelectScreen from '../screens/Consultation/LanguageSelectScreen';
import InterviewScreen from '../screens/Consultation/InterviewScreen';
import DocumentUploadScreen from '../screens/Documents/DocumentUploadScreen';
import DocumentListScreen from '../screens/Documents/DocumentListScreen';
import DocumentExtractionScreen from '../screens/Documents/DocumentExtractionScreen';
import TimelineScreen from '../screens/Timeline/TimelineScreen';
import ClinicalSummaryScreen from '../screens/Summary/ClinicalSummaryScreen';
import ProfileScreen from '../screens/Profile/ProfileScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();

export const RootNavigator: React.FC = () => {
  const { isAuthenticated, isLoading } = usePatient();

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
        // Auth Stack
        <Stack.Group>
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Register" component={RegisterScreen} />
        </Stack.Group>
      ) : (
        // Authenticated Protected Patient Stack
        <Stack.Group>
          <Stack.Screen name="Home" component={HomeScreen} />
          <Stack.Screen name="HospitalSelect" component={HospitalSelectScreen} />
          <Stack.Screen name="Consent" component={ConsentScreen} />
          <Stack.Screen name="LanguageSelect" component={LanguageSelectScreen} />
          <Stack.Screen name="Interview" component={InterviewScreen} />
          <Stack.Screen name="DocumentUpload" component={DocumentUploadScreen} />
          <Stack.Screen name="DocumentList" component={DocumentListScreen} />
          <Stack.Screen name="DocumentExtraction" component={DocumentExtractionScreen} />
          <Stack.Screen name="Timeline" component={TimelineScreen} />
          <Stack.Screen name="ClinicalSummary" component={ClinicalSummaryScreen} />
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
