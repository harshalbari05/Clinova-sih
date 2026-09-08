import secureStorage from '../storage/secureStore';
import * as SecureStore from 'expo-secure-store';

describe('SecureStore Token Storage Logic', () => {
  beforeEach(async () => {
    await secureStorage.clearAll();
    jest.clearAllMocks();
  });

  it('correctly persists and retrieves JWT access token via SecureStore', async () => {
    const testToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test-patient-token';
    await secureStorage.setItem('clinova_patient_token', testToken);

    expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
      'clinova_patient_token',
      testToken,
      expect.objectContaining({ keychainAccessible: 1 })
    );

    const retrieved = await secureStorage.getItem('clinova_patient_token');
    expect(retrieved).toBe(testToken);
  });

  it('correctly deletes token on logout', async () => {
    await secureStorage.setItem('clinova_patient_token', 'temp-token');
    await secureStorage.deleteItem('clinova_patient_token');

    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('clinova_patient_token');
    const retrieved = await secureStorage.getItem('clinova_patient_token');
    expect(retrieved).toBeNull();
  });

  it('clears all session credentials safely on clearAll', async () => {
    await secureStorage.setItem('clinova_patient_token', 'token-123');
    await secureStorage.setItem('clinova_selected_language', 'Hindi');
    await secureStorage.clearAll();

    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('clinova_patient_token');
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('clinova_selected_language');
  });
});
