/**
 * Hardware-backed Secure Storage Service
 * Uses expo-secure-store with an in-memory fallback for test and non-native environments.
 * Strictly avoids storing passwords or unencrypted credentials.
 */
import * as SecureStore from 'expo-secure-store';

const memoryFallback = new Map<string, string>();

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'clinova_patient_access_token',
  USER_ID: 'clinova_patient_user_id',
  PATIENT_ID: 'clinova_patient_patient_id',
  ACTIVE_CONSULTATION_ID: 'clinova_active_consultation_id',
  ACTIVE_LANGUAGE: 'clinova_active_language',
} as const;

export const setSecureItem = async (key: string, value: string): Promise<void> => {
  try {
    const isAvailable = await SecureStore.isAvailableAsync().catch(() => false);
    if (isAvailable) {
      await SecureStore.setItemAsync(key, value);
    } else {
      memoryFallback.set(key, value);
    }
  } catch {
    memoryFallback.set(key, value);
  }
};

export const getSecureItem = async (key: string): Promise<string | null> => {
  try {
    const isAvailable = await SecureStore.isAvailableAsync().catch(() => false);
    if (isAvailable) {
      return await SecureStore.getItemAsync(key);
    }
    return memoryFallback.get(key) || null;
  } catch {
    return memoryFallback.get(key) || null;
  }
};

export const deleteSecureItem = async (key: string): Promise<void> => {
  try {
    const isAvailable = await SecureStore.isAvailableAsync().catch(() => false);
    if (isAvailable) {
      await SecureStore.deleteItemAsync(key);
    }
    memoryFallback.delete(key);
  } catch {
    memoryFallback.delete(key);
  }
};

export const removeSecureItem = deleteSecureItem;

export const clearSessionStorage = async (): Promise<void> => {
  await Promise.all([
    deleteSecureItem(STORAGE_KEYS.ACCESS_TOKEN),
    deleteSecureItem(STORAGE_KEYS.USER_ID),
    deleteSecureItem(STORAGE_KEYS.PATIENT_ID),
    deleteSecureItem(STORAGE_KEYS.ACTIVE_CONSULTATION_ID),
  ]);
};
