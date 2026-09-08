import axios from 'axios';
import { Platform } from 'react-native';
import { secureStorage } from '../storage/secureStore';

/**
 * Resolves the default API base URL depending on platform:
 * - Environment override: process.env.EXPO_PUBLIC_API_URL
 * - Android Emulator: http://10.0.2.2:8000/api/v1
 * - iOS Simulator / Web / Default: http://localhost:8000/api/v1
 */
export const getApiBaseUrl = (): string => {
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000/api/v1';
  }
  return 'http://localhost:8000/api/v1';
};

export const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Listener type for 401 unauthorized notifications
type AuthExpiredListener = () => void;
const authExpiredListeners: AuthExpiredListener[] = [];

export const onAuthExpired = (listener: AuthExpiredListener) => {
  authExpiredListeners.push(listener);
  return () => {
    const idx = authExpiredListeners.indexOf(listener);
    if (idx !== -1) authExpiredListeners.splice(idx, 1);
  };
};

// Interceptor: Attach JWT token from secure storage
api.interceptors.request.use(async (config) => {
  const token = await secureStorage.getItem('clinova_patient_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor: Handle 401 token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await secureStorage.deleteItem('clinova_patient_token');
      await secureStorage.deleteItem('clinova_user_data');
      await secureStorage.deleteItem('clinova_patient_data');
      authExpiredListeners.forEach((listener) => listener());
    }
    return Promise.reject(error);
  }
);

export default api;
