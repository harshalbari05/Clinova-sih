/**
 * Runtime Device Permissions Service
 * Handles Camera, Microphone, and Photo Library permissions with graceful denial fallbacks.
 */
import { Camera } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { Audio } from 'expo-av';

export const permissions = {
  async requestCameraPermission(): Promise<boolean> {
    try {
      const { status } = await Camera.requestCameraPermissionsAsync();
      return status === 'granted';
    } catch {
      return false;
    }
  },

  async requestMicrophonePermission(): Promise<boolean> {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      return status === 'granted';
    } catch {
      return false;
    }
  },

  async requestMediaLibraryPermission(): Promise<boolean> {
    try {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      return status === 'granted';
    } catch {
      return false;
    }
  },

  async checkPermissionsStatus() {
    const [camera, mic, media] = await Promise.all([
      Camera.getCameraPermissionsAsync().catch(() => ({ granted: false })),
      Audio.getPermissionsAsync().catch(() => ({ granted: false })),
      ImagePicker.getMediaLibraryPermissionsAsync().catch(() => ({ granted: false })),
    ]);

    return {
      cameraGranted: camera.granted,
      microphoneGranted: mic.granted,
      mediaLibraryGranted: media.granted,
    };
  },
};
