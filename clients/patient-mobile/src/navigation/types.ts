/**
 * Navigation Type Definitions for Clinova Patient Mobile
 */
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';

export type RootStackParamList = {
  // Pre-Auth Screens
  OnboardingLanguage: undefined;
  Login: undefined;
  Register: undefined;

  // Consent (standalone — not tied to hospital)
  Consent: undefined;

  // Main Patient Dashboard & Care Flow
  Home: undefined;
  HospitalSelect: undefined; // kept for future hospital-side use, removed from onboarding
  LanguageSelect: { consultationId?: string }; // consultationId optional — absent = interview setup flow
  Interview: { consultationId: string; language?: string };
  DocumentList: { consultationId?: string };
  DocumentUpload: { consultationId?: string };
  DocumentExtraction: { documentId: string };
  Timeline: undefined;
  ClinicalSummary: { consultationId: string };
  PatientQR: undefined;
  Profile: undefined;
};

export type NavigationProp<T extends keyof RootStackParamList> = NativeStackNavigationProp<
  RootStackParamList,
  T
>;

export type ScreenRouteProp<T extends keyof RootStackParamList> = RouteProp<
  RootStackParamList,
  T
>;
