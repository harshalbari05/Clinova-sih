import { vi } from 'vitest';

// Mock Expo SecureStore
const mockStorage: Record<string, string> = {};
vi.mock('expo-secure-store', () => ({
  getItemAsync: vi.fn(async (key: string) => mockStorage[key] || null),
  setItemAsync: vi.fn(async (key: string, value: string) => {
    mockStorage[key] = value;
  }),
  deleteItemAsync: vi.fn(async (key: string) => {
    delete mockStorage[key];
  }),
}));

// Mock Expo Permissions & Media
vi.mock('expo-camera', () => ({
  CameraView: () => null,
  useCameraPermissions: () => [{ granted: true }, vi.fn()],
}));

vi.mock('expo-image-picker', () => ({
  requestMediaLibraryPermissionsAsync: vi.fn(async () => ({ granted: true })),
  launchImageLibraryAsync: vi.fn(async () => ({
    canceled: false,
    assets: [{ uri: 'file://test/scan.jpg', fileName: 'scan.jpg' }],
  })),
}));

vi.mock('expo-av', () => ({
  Audio: {
    requestPermissionsAsync: vi.fn(async () => ({ granted: true, status: 'granted' })),
    getPermissionsAsync: vi.fn(async () => ({ granted: true, status: 'granted' })),
    setAudioModeAsync: vi.fn(async () => {}),
  },
}));

// Mock React Native basic components
vi.mock('react-native', () => ({
  Platform: { OS: 'android', select: (obj: any) => obj.android || obj.default },
  StyleSheet: {
    create: (styles: any) => styles,
    absoluteFill: {},
  },
  View: 'View',
  Text: 'Text',
  TouchableOpacity: 'TouchableOpacity',
  TextInput: 'TextInput',
  ScrollView: 'ScrollView',
  ActivityIndicator: 'ActivityIndicator',
  Modal: 'Modal',
  Alert: {
    alert: vi.fn(),
  },
  RefreshControl: 'RefreshControl',
  Image: 'Image',
  SafeAreaView: 'SafeAreaView',
}));
