import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AuthResponse, Consultation, Hospital, Patient, AISession, TriageResult, User } from '../types';
import { authApi } from '../api';

interface PatientContextType {
  token: string | null;
  user: User | null;
  patient: Patient | null;
  currentPatient: Patient | null;
  isAuthenticated: boolean;
  selectedHospital: Hospital | null;
  activeHospital: Hospital | null;
  activeConsultation: Consultation | null;
  currentConsultation: Consultation | null;
  activeSession: AISession | null;
  language: string;
  consentGiven: boolean;
  triageAlert: TriageResult | null;

  // Actions
  login: (authData: AuthResponse) => void;
  logout: () => void;
  setSelectedHospital: (hospital: Hospital | null) => void;
  setActiveConsultation: (consultation: Consultation | null) => void;
  setActiveSession: (session: AISession | null) => void;
  setLanguage: (lang: string) => void;
  setConsentGiven: (given: boolean) => void;
  setTriageAlert: (alert: TriageResult | null) => void;
  refreshProfile: () => Promise<void>;
  clearIntake: () => void;
}

const PatientContext = createContext<PatientContextType | null>(null);

export const PatientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('clinova_patient_token'));
  
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem('clinova_user_data');
    return raw ? JSON.parse(raw) : null;
  });

  const [patient, setPatient] = useState<Patient | null>(() => {
    const raw = localStorage.getItem('clinova_patient_data');
    return raw ? JSON.parse(raw) : null;
  });

  const [selectedHospital, setSelectedHospitalState] = useState<Hospital | null>(() => {
    const raw = localStorage.getItem('clinova_selected_hospital');
    return raw ? JSON.parse(raw) : null;
  });

  const [activeConsultation, setActiveConsultationState] = useState<Consultation | null>(() => {
    const raw = localStorage.getItem('clinova_active_consultation');
    return raw ? JSON.parse(raw) : null;
  });

  const [activeSession, setActiveSessionState] = useState<AISession | null>(() => {
    const raw = localStorage.getItem('clinova_active_session');
    return raw ? JSON.parse(raw) : null;
  });

  const [language, setLanguageState] = useState<string>(() => {
    return localStorage.getItem('clinova_selected_language') || 'English';
  });

  const [consentGiven, setConsentGiven] = useState<boolean>(() => {
    return localStorage.getItem('clinova_consent_given') === 'true';
  });

  const [triageAlert, setTriageAlert] = useState<TriageResult | null>(null);

  // Sync state helpers with localStorage
  const setSelectedHospital = useCallback((h: Hospital | null) => {
    setSelectedHospitalState(h);
    if (h) {
      localStorage.setItem('clinova_selected_hospital', JSON.stringify(h));
    } else {
      localStorage.removeItem('clinova_selected_hospital');
    }
  }, []);

  const setActiveConsultation = useCallback((c: Consultation | null) => {
    setActiveConsultationState(c);
    if (c) {
      localStorage.setItem('clinova_active_consultation', JSON.stringify(c));
    } else {
      localStorage.removeItem('clinova_active_consultation');
    }
  }, []);

  const setActiveSession = useCallback((s: AISession | null) => {
    setActiveSessionState(s);
    if (s) {
      localStorage.setItem('clinova_active_session', JSON.stringify(s));
    } else {
      localStorage.removeItem('clinova_active_session');
    }
  }, []);

  const setLanguage = useCallback((lang: string) => {
    setLanguageState(lang);
    localStorage.setItem('clinova_selected_language', lang);
  }, []);

  const updateConsentGiven = useCallback((given: boolean) => {
    setConsentGiven(given);
    localStorage.setItem('clinova_consent_given', given ? 'true' : 'false');
  }, []);

  const login = useCallback((authData: AuthResponse) => {
    setToken(authData.access_token);
    setUser(authData.user);
    if (authData.patient) {
      setPatient(authData.patient);
    }
    localStorage.setItem('clinova_patient_token', authData.access_token);
    localStorage.setItem('clinova_user_data', JSON.stringify(authData.user));
    if (authData.patient) {
      localStorage.setItem('clinova_patient_data', JSON.stringify(authData.patient));
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setPatient(null);
    setSelectedHospitalState(null);
    setActiveConsultationState(null);
    setActiveSessionState(null);
    setConsentGiven(false);
    setTriageAlert(null);
    localStorage.removeItem('clinova_patient_token');
    localStorage.removeItem('clinova_user_data');
    localStorage.removeItem('clinova_patient_data');
    localStorage.removeItem('clinova_selected_hospital');
    localStorage.removeItem('clinova_active_consultation');
    localStorage.removeItem('clinova_active_session');
    localStorage.removeItem('clinova_consent_given');
  }, []);

  const clearIntake = useCallback(() => {
    setActiveConsultationState(null);
    setActiveSessionState(null);
    setConsentGiven(false);
    setTriageAlert(null);
    localStorage.removeItem('clinova_active_consultation');
    localStorage.removeItem('clinova_active_session');
    localStorage.removeItem('clinova_consent_given');
  }, []);

  const refreshProfile = useCallback(async () => {
    if (!token) return;
    try {
      const p = await authApi.getPatientProfile();
      setPatient(p);
      localStorage.setItem('clinova_patient_data', JSON.stringify(p));
    } catch {
      // If token expired, logout
      logout();
    }
  }, [token, logout]);

  // Check and refresh profile on mount if token exists
  useEffect(() => {
    if (token && !patient) {
      refreshProfile();
    }
  }, [token, patient, refreshProfile]);

  return (
    <PatientContext.Provider
      value={{
        token,
        user,
        patient,
        currentPatient: patient,
        isAuthenticated: !!token,
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
        setConsentGiven: updateConsentGiven,
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
