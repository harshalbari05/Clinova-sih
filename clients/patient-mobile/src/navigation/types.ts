/**
 * Navigation Type Definitions for Clinova Patient Mobile
 */
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';

export type RootStackParamList = {
  // Auth Screens
  Login: undefined;
  Register: undefined;

  // Main Patient Intake & Care Flow
  Home: undefined;
  HospitalSelect: undefined;
  Consent: { hospitalId: string };
  LanguageSelect: { consultationId: string };
  Interview: { consultationId: string; language?: string };
  DocumentList: { consultationId?: string };
  DocumentUpload: { consultationId?: string };
  DocumentExtraction: { documentId: string };
  Timeline: undefined;
  ClinicalSummary: { consultationId: string };
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
