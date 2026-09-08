import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AuthResponse, Consultation, Hospital, Patient, AISession, TriageResult, User } from '../types';
import { authApi, onAuthExpired } from '../api';
import secureStorage from '../storage/secureStore';

interface PatientContextType {
  token: string | null;
  user: User | null;
  patient: Patient | null;
  currentPatient: Patient | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  selectedHospital: Hospital | null;
  activeHospital: Hospital | null;
  activeConsultation: Consultation | null;
  currentConsultation: Consultation | null;
  activeSession: AISession | null;
  language: string;
  consentGiven: boolean;
  triageAlert: TriageResult | null;

  // Actions
  login: (authData: AuthResponse) => Promise<void>;
  logout: () => Promise<void>;
  setSelectedHospital: (hospital: Hospital | null) => Promise<void>;
  setActiveConsultation: (consultation: Consultation | null) => Promise<void>;
  setActiveSession: (session: AISession | null) => Promise<void>;
  setLanguage: (lang: string) => Promise<void>;
  setConsentGiven: (given: boolean) => Promise<void>;
  setTriageAlert: (alert: TriageResult | null) => void;
  refreshProfile: () => Promise<void>;
  clearIntake: () => Promise<void>;
}

const PatientContext = createContext<PatientContextType | null>(null);

export const PatientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [selectedHospital, setSelectedHospitalState] = useState<Hospital | null>(null);
  const [activeConsultation, setActiveConsultationState] = useState<Consultation | null>(null);
  const [activeSession, setActiveSessionState] = useState<AISession | null>(null);
  const [language, setLanguageState] = useState<string>('English');
  const [consentGiven, setConsentGivenState] = useState<boolean>(false);
  const [triageAlert, setTriageAlert] = useState<TriageResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Restore authenticated session on mount from SecureStore
  useEffect(() => {
    let isMounted = true;
    const restoreSession = async () => {
      try {
        const storedToken = await secureStorage.getItem('clinova_patient_token');
        const storedUser = await secureStorage.getItem('clinova_user_data');
        const storedPatient = await secureStorage.getItem('clinova_patient_data');
        const storedHospital = await secureStorage.getItem('clinova_selected_hospital');
        const storedConsultation = await secureStorage.getItem('clinova_active_consultation');
        const storedSession = await secureStorage.getItem('clinova_active_session');
        const storedLang = await secureStorage.getItem('clinova_selected_language');
        const storedConsent = await secureStorage.getItem('clinova_consent_given');

        if (isMounted) {
          if (storedToken) setToken(storedToken);
          if (storedUser) setUser(JSON.parse(storedUser));
          if (storedPatient) setPatient(JSON.parse(storedPatient));
          if (storedHospital) setSelectedHospitalState(JSON.parse(storedHospital));
          if (storedConsultation) setActiveConsultationState(JSON.parse(storedConsultation));
          if (storedSession) setActiveSessionState(JSON.parse(storedSession));
          if (storedLang) setLanguageState(storedLang);
          if (storedConsent) setConsentGivenState(storedConsent === 'true');
        }
      } catch (err) {
        // Fallback gracefully on initialization error
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    restoreSession();

    // Listen for 401 unauthorized token expirations
    const unsubscribe = onAuthExpired(() => {
      logout();
    });

    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, []);

  const setSelectedHospital = useCallback(async (h: Hospital | null) => {
    setSelectedHospitalState(h);
    if (h) {
      await secureStorage.setItem('clinova_selected_hospital', JSON.stringify(h));
    } else {
      await secureStorage.deleteItem('clinova_selected_hospital');
    }
  }, []);

  const setActiveConsultation = useCallback(async (c: Consultation | null) => {
    setActiveConsultationState(c);
    if (c) {
      await secureStorage.setItem('clinova_active_consultation', JSON.stringify(c));
    } else {
      await secureStorage.deleteItem('clinova_active_consultation');
    }
  }, []);

  const setActiveSession = useCallback(async (s: AISession | null) => {
    setActiveSessionState(s);
    if (s) {
      await secureStorage.setItem('clinova_active_session', JSON.stringify(s));
    } else {
      await secureStorage.deleteItem('clinova_active_session');
    }
  }, []);

  const setLanguage = useCallback(async (lang: string) => {
    setLanguageState(lang);
    await secureStorage.setItem('clinova_selected_language', lang);
  }, []);

  const setConsentGiven = useCallback(async (given: boolean) => {
    setConsentGivenState(given);
    await secureStorage.setItem('clinova_consent_given', given ? 'true' : 'false');
  }, []);

  const login = useCallback(async (authData: AuthResponse) => {
    setToken(authData.access_token);
    setUser(authData.user);
    if (authData.patient) {
      setPatient(authData.patient);
    }
    await secureStorage.setItem('clinova_patient_token', authData.access_token);
    await secureStorage.setItem('clinova_user_data', JSON.stringify(authData.user));
    if (authData.patient) {
      await secureStorage.setItem('clinova_patient_data', JSON.stringify(authData.patient));
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore network errors on logout
    }
    setToken(null);
    setUser(null);
    setPatient(null);
    setSelectedHospitalState(null);
    setActiveConsultationState(null);
    setActiveSessionState(null);
    setConsentGivenState(false);
    setTriageAlert(null);
    await secureStorage.clearAll();
  }, []);

  const clearIntake = useCallback(async () => {
    setActiveConsultationState(null);
    setActiveSessionState(null);
    setConsentGivenState(false);
    setTriageAlert(null);
    await secureStorage.deleteItem('clinova_active_consultation');
    await secureStorage.deleteItem('clinova_active_session');
    await secureStorage.deleteItem('clinova_consent_given');
  }, []);

  const refreshProfile = useCallback(async () => {
    if (!token) return;
    try {
      const p = await authApi.getPatientProfile();
      setPatient(p);
      await secureStorage.setItem('clinova_patient_data', JSON.stringify(p));
    } catch {
      // If unauthorized, token expired
      await logout();
    }
  }, [token, logout]);

  return (
    <PatientContext.Provider
      value={{
        token,
        user,
        patient,
        currentPatient: patient,
        isAuthenticated: !!token,
        isLoading,
        selectedHospital,
        activeHospital: selectedHospital,
        activeConsultation,
        currentConsultation: activeConsultation,
        activeSession,
        language,
        consentGiven,
        triageAlert,
        login,
        logout,
        setSelectedHospital,
        setActiveConsultation,
        setActiveSession,
        setLanguage,
        setConsentGiven,
        setTriageAlert,
        refreshProfile,
        clearIntake,
      }}
    >
      {children}
    </PatientContext.Provider>
  );
};

export const usePatient = (): PatientContextType => {
  const ctx = useContext(PatientContext);
  if (!ctx) {
    throw new Error('usePatient must be used within a PatientProvider');
  }
  return ctx;
};

export default PatientContext;
