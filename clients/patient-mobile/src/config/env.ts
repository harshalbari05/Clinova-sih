/**
 * Clinova Mobile Environment & Network Configuration
 * Handles dynamic API routing for Android emulator (10.0.2.2), physical devices (LAN IP), and localhost.
 */
import { Platform } from 'react-native';

// Default development URLs
const DEFAULT_EMULATOR_URL = 'http://10.0.2.2:8000/api/v1';
const DEFAULT_LOCAL_URL = 'http://localhost:8000/api/v1';

let overrideApiUrl: string | null = null;

export const getApiBaseUrl = (): string => {
  // 1. Explicit user/runtime override (e.g. from developer settings or test runner)
  if (overrideApiUrl) {
    return overrideApiUrl;
  }

  // 2. Build-time environment variable (e.g. EXPO_PUBLIC_API_URL in .env)
  if (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }

  // 3. Android Emulator uses 10.0.2.2 to reach host machine localhost
  if (Platform.OS === 'android') {
    return DEFAULT_EMULATOR_URL;
  }

  // 4. Default for iOS simulator, Web, and node tests
  return DEFAULT_LOCAL_URL;
};

/**
 * Configure API base URL dynamically at runtime (useful for physical phone on local LAN)
 */
export const setApiBaseUrl = (url: string | null): void => {
  overrideApiUrl = url;
};

export const getNetworkDiagnostics = () => {
  return {
    activeBaseUrl: getApiBaseUrl(),
    platform: Platform.OS,
    isOverridden: !!overrideApiUrl,
  };
};
