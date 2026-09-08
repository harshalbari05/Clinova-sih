// Jest setup file for Clinova Patient Mobile

// Mock expo-secure-store
jest.mock('expo-secure-store', () => {
  const store = {};
  return {
    isAvailableAsync: jest.fn().mockResolvedValue(true),
    setItemAsync: jest.fn().mockImplementation((k, v) => {
      store[k] = v;
      return Promise.resolve();
    }),
    getItemAsync: jest.fn().mockImplementation((k) => {
      return Promise.resolve(store[k] || null);
    }),
    deleteItemAsync: jest.fn().mockImplementation((k) => {
      delete store[k];
      return Promise.resolve();
    }),
    WHEN_UNLOCKED_THIS_DEVICE_ONLY: 1,
  };
});

// Mock expo-av
jest.mock('expo-av', () => ({
  Audio: {
    getPermissionsAsync: jest.fn().mockResolvedValue({ status: 'granted' }),
    requestPermissionsAsync: jest.fn().mockResolvedValue({ status: 'granted' }),
    setAudioModeAsync: jest.fn().mockResolvedValue(true),
    Recording: {
      createAsync: jest.fn().mockResolvedValue({
        recording: {
          stopAndUnloadAsync: jest.fn().mockResolvedValue(true),
          getURI: jest.fn().mockReturnValue('file:///test-audio.m4a'),
        },
      }),
    },
    RecordingOptionsPresets: {
      HIGH_QUALITY: {},
    },
  },
}));

// Mock expo-image-picker
jest.mock('expo-image-picker', () => ({
  requestCameraPermissionsAsync: jest.fn().mockResolvedValue({ granted: true }),
  requestMediaLibraryPermissionsAsync: jest.fn().mockResolvedValue({ granted: true }),
  launchCameraAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: 'file:///captured.jpg', fileName: 'captured.jpg', mimeType: 'image/jpeg' }],
  }),
  launchImageLibraryAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: 'file:///gallery.jpg', fileName: 'gallery.jpg', mimeType: 'image/jpeg' }],
  }),
  MediaTypeOptions: { Images: 'Images' },
}));

// Mock expo-document-picker
jest.mock('expo-document-picker', () => ({
  getDocumentAsync: jest.fn().mockResolvedValue({
    canceled: false,
    assets: [{ uri: 'file:///doc.pdf', name: 'doc.pdf', mimeType: 'application/pdf' }],
  }),
}));
