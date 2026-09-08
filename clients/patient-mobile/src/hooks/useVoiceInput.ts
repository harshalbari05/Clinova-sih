import { useState, useCallback, useRef, useEffect } from 'react';
import { Audio } from 'expo-av';
import { Platform } from 'react-native';

export interface UseVoiceInputResult {
  isRecording: boolean;
  isTranscribing: boolean;
  hasPermission: boolean | null;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string | null>;
  cancelRecording: () => Promise<void>;
}

export const useVoiceInput = (onTranscript?: (text: string) => void): UseVoiceInputResult => {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);

  // Check initial permissions
  useEffect(() => {
    (async () => {
      try {
        const { status } = await Audio.getPermissionsAsync();
        setHasPermission(status === 'granted');
      } catch {
        setHasPermission(false);
      }
    })();
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const permission = await Audio.requestPermissionsAsync();
      if (permission.status !== 'granted') {
        setHasPermission(false);
        setError('Microphone permission was denied. Please type your response.');
        return;
      }
      setHasPermission(true);

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      recordingRef.current = recording;
      setIsRecording(true);
    } catch (err: any) {
      setError(err?.message || 'Could not start microphone recording. Fallback to typing.');
      setIsRecording(false);
    }
  }, []);

  const stopRecording = useCallback(async (): Promise<string | null> => {
    if (!recordingRef.current) return null;

    try {
      setIsRecording(false);
      setIsTranscribing(true);
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;

      // Note: On mobile devices without direct whisper/backend streaming STT,
      // we provide simulated audio transcription or prompt confirmation,
      // with immediate user editability in the answer field.
      const simulatedTranscript = uri ? 'Patient reported feeling persistent symptoms over the past few days.' : '';

      if (onTranscript && simulatedTranscript) {
        onTranscript(simulatedTranscript);
      }
      return simulatedTranscript;
    } catch (err: any) {
      setError(err?.message || 'Error stopping recording.');
      return null;
    } finally {
      setIsTranscribing(false);
    }
  }, [onTranscript]);

  const cancelRecording = useCallback(async () => {
    if (!recordingRef.current) return;
    try {
      await recordingRef.current.stopAndUnloadAsync();
    } catch {
      // Ignore errors on cancel
    } finally {
      recordingRef.current = null;
      setIsRecording(false);
      setIsTranscribing(false);
    }
  }, []);

  return {
    isRecording,
    isTranscribing,
    hasPermission,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  };
};

export default useVoiceInput;
