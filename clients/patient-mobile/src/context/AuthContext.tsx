/**
 * Authentication Context for Clinova Patient Mobile
 * Handles session restoration on launch, login, registration, and logout.
 */
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, Patient } from '../types';
import { api } from '../services/api';
import {
  setSecureItem,
  getSecureItem,
  clearSessionStorage,
  STORAGE_KEYS,
} from '../services/storage';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  patient: Patient | null;
  login: (credentials: { email?: string; password?: string; phone?: string; abha_id?: string }) => Promise<void>;
  register: (data: {
    email: string;
    password?: string;
    full_name: string;
    phone?: string;
    abha_id?: string;
    dob?: string;
    gender?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [user, setUser] = useState<User | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);

  const restoreSession = async () => {
    try {
      setIsLoading(true);
      const token = await getSecureItem(STORAGE_KEYS.ACCESS_TOKEN);
      if (!token) {
        setIsAuthenticated(false);
        setUser(null);
        setPatient(null);
        return;
      }

      // Validate session with backend
      const profile = await api.getMyProfile();
      setPatient(profile);
      setUser({
        id: profile.user_id,
        email: '',
        role: 'patient',
        is_active: true,
      });
      setIsAuthenticated(true);
    } catch {
      // Token expired, network error, or invalid session
      await clearSessionStorage();
      setIsAuthenticated(false);
      setUser(null);
      setPatient(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    restoreSession();
  }, []);

  const login = async (credentials: {
    email?: string;
    password?: string;
    phone?: string;
    abha_id?: string;
  }) => {
    setIsLoading(true);
    try {
      const response = await api.loginPatient(credentials);
      await setSecureItem(STORAGE_KEYS.ACCESS_TOKEN, response.access_token);
      await setSecureItem(STORAGE_KEYS.USER_ID, response.user.id);
      if (response.patient) {
        await setSecureItem(STORAGE_KEYS.PATIENT_ID, response.patient.id);
        setPatient(response.patient);
      }
      setUser(response.user);
      setIsAuthenticated(true);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: {
    email: string;
    password?: string;
    full_name: string;
    phone?: string;
    abha_id?: string;
    dob?: string;
    gender?: string;
  }) => {
    setIsLoading(true);
    try {
      const response = await api.registerPatient(data);
      await setSecureItem(STORAGE_KEYS.ACCESS_TOKEN, response.access_token);
      await setSecureItem(STORAGE_KEYS.USER_ID, response.user.id);
      if (response.patient) {
        await setSecureItem(STORAGE_KEYS.PATIENT_ID, response.patient.id);
        setPatient(response.patient);
      }
      setUser(response.user);
      setIsAuthenticated(true);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await clearSessionStorage();
      setIsAuthenticated(false);
      setUser(null);
      setPatient(null);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshProfile = async () => {
    try {
      const profile = await api.getMyProfile();
      setPatient(profile);
    } catch {
      // Profile refresh error handled gracefully
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        patient,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
