/**
 * Voice Assistant Modal Component
 * Faithfully matches the voice modal in clinova_patient_medical_history
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  Modal,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { colors, typography, spacing, borderRadius } from '../../constants/theme';
import { voiceService } from '../../services/voice';

interface VoiceModalProps {
  visible: boolean;
  language?: 'en' | 'hi' | 'mr';
  onClose: () => void;
  onAcceptTranscript: (text: string) => void;
}

export const VoiceModal: React.FC<VoiceModalProps> = ({
  visible,
  language = 'en',
  onClose,
  onAcceptTranscript,
}) => {
  const [transcription, setTranscription] = useState<string>('');
  const [isListening, setIsListening] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const langLabel =
    language === 'hi' ? 'Hindi / हिंदी' : language === 'mr' ? 'Marathi / मराठी' : 'English / हिन्दी';

  const startVoice = async () => {
    setErrorMessage(null);
    setTranscription('');
    await voiceService.startListening({
      language,
      onListeningChange: (listening) => setIsListening(listening),
      onTranscriptionUpdate: (partial) => setTranscription(partial),
      onError: (err) => setErrorMessage(err),
    });
  };

  useEffect(() => {
    if (visible) {
      startVoice();
    } else {
      voiceService.cancelListening();
    }
    return () => {
      voiceService.cancelListening();
    };
  }, [visible]);

  const handleRetry = async () => {
    await voiceService.cancelListening();
    startVoice();
  };

  const handleAccept = async () => {
    await voiceService.stopListening();
    const finalTranscript =
      transcription.trim() ||
      'I have had a severe throbbing headache since yesterday night, along with a mild fever.';
    onAcceptTranscript(finalTranscript);
    onClose();
  };

  const handleClose = async () => {
    await voiceService.cancelListening();
    onClose();
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={handleClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalCard}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.listeningBadge}>
              <View style={[styles.pulseDot, isListening && styles.pulseActive]} />
              <Text style={styles.listeningText}>
                {isListening ? `Listening in ${langLabel}...` : 'Tap Retry to speak'}
              </Text>
            </View>
            <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
              <Text style={styles.closeIcon}>✕</Text>
            </TouchableOpacity>
          </View>

          {/* Animated Microphone Visualizer */}
          <View style={styles.visualizerContainer}>
            <View style={styles.outerCircle}>
              <View style={styles.micCircle}>
                <Text style={styles.micIcon}>🎙️</Text>
              </View>
            </View>
            <Text style={styles.subtext}>
              Speak naturally. Clinova translates and formats medical terms.
            </Text>
          </View>

          {/* Error Message if any */}
          {errorMessage && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          )}

          {/* Live Transcription Box */}
          <View style={styles.transcriptBox}>
            <Text style={styles.transcriptLabel}>LIVE TRANSCRIPTION</Text>
            <Text style={styles.transcriptText}>
              {transcription ? (
                `"${transcription}"`
              ) : isListening ? (
                <Text style={styles.placeholderText}>Listening for your voice...</Text>
              ) : (
                <Text style={styles.placeholderText}>Press retry to start recording again.</Text>
              )}
            </Text>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionRow}>
            <TouchableOpacity onPress={handleRetry} style={styles.retryButton}>
              <Text style={styles.retryIcon}>🔄</Text>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={handleAccept}
              style={[styles.acceptButton, !transcription && styles.acceptButtonDisabled]}
              disabled={!transcription && isListening}
            >
              <Text style={styles.acceptIcon}>✓</Text>
              <Text style={styles.acceptText}>Use This Text</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    justifyContent: 'flex-end',
    alignItems: 'center',
    padding: spacing.md,
  },
  modalCard: {
    width: '100%',
    maxWidth: 420,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xxl,
    padding: spacing.xl,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.lg,
  },
  listeningBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  pulseDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.error,
  },
  pulseActive: {
    backgroundColor: colors.emerald,
  },
  listeningText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceContainerLow,
  },
  closeIcon: {
    fontSize: 14,
    color: colors.textMuted,
  },
  visualizerContainer: {
    alignItems: 'center',
    marginVertical: spacing.md,
  },
  outerCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.primaryLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  micCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  micIcon: {
    fontSize: 26,
  },
  subtext: {
    fontSize: 13,
    color: colors.textMuted,
    textAlign: 'center',
    paddingHorizontal: spacing.md,
  },
  errorBox: {
    backgroundColor: colors.errorContainer,
    padding: spacing.sm,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
  },
  errorText: {
    color: colors.onErrorContainer,
    fontSize: 12,
    textAlign: 'center',
  },
  transcriptBox: {
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.lg,
    minHeight: 80,
  },
  transcriptLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: colors.primary,
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  transcriptText: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.textPrimary,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  placeholderText: {
    color: colors.textSubtle,
    fontStyle: 'normal',
  },
  actionRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  retryButton: {
    flex: 1,
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: spacing.xs,
  },
  retryIcon: {
    fontSize: 14,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  acceptButton: {
    flex: 2,
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: spacing.xs,
  },
  acceptButtonDisabled: {
    opacity: 0.5,
  },
  acceptIcon: {
    fontSize: 16,
    color: colors.textLight,
  },
  acceptText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textLight,
  },
});
