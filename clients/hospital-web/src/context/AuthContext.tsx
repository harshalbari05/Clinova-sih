import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserSummary, HospitalSummary } from '../types/auth';
import { loginHospital, getMe, logout as apiLogout } from '../api/auth';

interface AuthContextType {
  user: UserSummary | null;
  hospital: HospitalSummary | null;
  hospitalRole: string | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserSummary | null>(() => {
    const saved = localStorage.getItem('clinova_hospital_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [hospital, setHospital] = useState<HospitalSummary | null>(() => {
    const saved = localStorage.getItem('clinova_hospital_info');
    return saved ? JSON.parse(saved) : null;
  });

  const [hospitalRole, setHospitalRole] = useState<string | null>(() => {
    return localStorage.getItem('clinova_hospital_role');
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('clinova_hospital_token');
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function verifySession() {
      const storedToken = localStorage.getItem('clinova_hospital_token');
      if (storedToken) {
        try {
          const current = await getMe();
          if (current.account_type === 'hospital') {
            setUser(current.user);
            setHospital(current.hospital || null);
            setHospitalRole(current.hospital_role || null);
            localStorage.setItem('clinova_hospital_user', JSON.stringify(current.user));
            if (current.hospital) {
              localStorage.setItem('clinova_hospital_info', JSON.stringify(current.hospital));
            }
            if (current.hospital_role) {
              localStorage.setItem('clinova_hospital_role', current.hospital_role);
            }
          } else {
            // Patient account attempting hospital login -> invalidate
            await apiLogout();
            setUser(null);
            setHospital(null);
            setHospitalRole(null);
            setToken(null);
          }
        } catch {
          // Token expired or invalid
          setUser(null);
          setHospital(null);
          setHospitalRole(null);
          setToken(null);
        }
      }
      setIsLoading(false);
    }
    verifySession();
  }, []);

  const login = async (identifier: string, password: string) => {
    const response = await loginHospital(identifier, password);
    setToken(response.access_token);
    setUser(response.user);
    setHospital(response.hospital || null);
    setHospitalRole(response.hospital_role || null);

    localStorage.setItem('clinova_hospital_token', response.access_token);
    localStorage.setItem('clinova_hospital_user', JSON.stringify(response.user));
    if (response.hospital) {
      localStorage.setItem('clinova_hospital_info', JSON.stringify(response.hospital));
    }
    if (response.hospital_role) {
      localStorage.setItem('clinova_hospital_role', response.hospital_role);
    }
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch {
      // Ignore network errors on logout
    } finally {
      setUser(null);
      setHospital(null);
      setHospitalRole(null);
      setToken(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        hospital,
        hospitalRole,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useOptionalAuth = (): AuthContextType | null => {
  return useContext(AuthContext) ?? null;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
