import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { NavigationProp, ScreenRouteProp } from '../../navigation/types';
import { usePatient } from '../../context/PatientContext';
import { aiApi, triageApi } from '../../api';
import { AIMessage, AISession, TriageResult } from '../../types';
import colors from '../../theme/colors';
import { borderRadius, spacing } from '../../theme/spacing';
import Header from '../../components/Header';
import Card from '../../components/Card';
import Button from '../../components/Button';
import Input from '../../components/Input';
import StepIndicator from '../../components/StepIndicator';
import EmergencyBanner from '../../components/EmergencyBanner';
import useVoiceInput from '../../hooks/useVoiceInput';

export const InterviewScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp<'Interview'>>();
  const route = useRoute<ScreenRouteProp<'Interview'>>();
  const { consultationId, language: routeLanguage } = route.params;

  const { language, activeSession, setActiveSession, triageAlert, setTriageAlert } = usePatient();
  const activeLang = routeLanguage || language || 'English';

  const [session, setSession] = useState<AISession | null>(activeSession);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loadingSession, setLoadingSession] = useState(true);
  const [sending, setSending] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);

  const scrollViewRef = useRef<ScrollView>(null);

  // Voice recording hook
  const {
    isRecording,
    isTranscribing,
    error: voiceError,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useVoiceInput((transcript) => {
    if (transcript) {
      setInputText((prev) => (prev ? `${prev} ${transcript}` : transcript));
    }
  });

  // 1. Initialize or restore AI interview session
  useEffect(() => {
    let isMounted = true;

    const initSession = async () => {
      try {
        setLoadingSession(true);
        setError(null);

        let curSession = activeSession;
        if (!curSession || curSession.consultation_id !== consultationId) {
          // Create new session with consultationId and selected language
          curSession = await aiApi.createSession(consultationId, activeLang);
          await setActiveSession(curSession);
        }

        if (isMounted) {
          setSession(curSession);
        }

        // Fetch session messages
        if (curSession) {
          const res = await aiApi.listMessages(curSession.id, 100, 0);
          if (isMounted) {
            setMessages(res.items || []);
            if (curSession.status === 'completed') {
              setIsCompleted(true);
            }
          }
        }

        // Check initial triage status
        try {
          const triage = await triageApi.getTriageResult(consultationId);
          if (triage && (triage.is_red_flag || triage.priority === 'red' || triage.priority === 'EMERGENCY')) {
            setTriageAlert(triage);
          }
        } catch {
          // Triage might be fresh
        }
      } catch (err: any) {
        if (isMounted) {
          const msg = err.response?.data?.detail || 'Failed to initialize AI interview. Please retry.';
          setError(msg);
        }
      } finally {
        if (isMounted) setLoadingSession(false);
      }
    };

    initSession();

    return () => {
      isMounted = false;
    };
  }, [consultationId, activeLang, setActiveSession, setTriageAlert]);

  // Scroll to bottom whenever messages update
  useEffect(() => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 150);
  }, [messages]);

  // 2. Submit patient response to backend AI interview engine
  const handleSendMessage = async () => {
    if (!inputText.trim() || !session || sending) return;

    const text = inputText.trim();
    setInputText('');
    setSending(true);
    setError(null);

    // Optimistically add patient message to UI
    const optimisticPatientMsg: AIMessage = {
      id: `temp-${Date.now()}`,
      session_id: session.id,
      role: 'patient',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticPatientMsg]);

    try {
      const response = await aiApi.sendMessage(session.id, text);

      // Re-fetch all chronological session messages from backend
      const updated = await aiApi.listMessages(session.id, 100, 0);
      setMessages(updated.items || []);

      if (response.is_complete) {
        setIsCompleted(true);
      }

      // Check authoritative backend triage evaluation after patient statement
      try {
        const triage = await triageApi.getTriageResult(consultationId);
        if (triage && (triage.is_red_flag || triage.priority === 'red' || triage.priority === 'EMERGENCY')) {
          setTriageAlert(triage);
        }
      } catch {
        // Continue interview
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to submit response. Please retry.';
      setError(msg);
    } finally {
      setSending(false);
    }
  };

  // 3. Mark session complete — show Clinical Summary (patient can upload docs separately from dashboard)
  const handleCompleteInterview = async () => {
    if (!session) return;
    try {
      setCompleting(true);
      await aiApi.completeSession(session.id);
      setIsCompleted(true);
      navigation.navigate('ClinicalSummary', { consultationId });
    } catch (err: any) {
      // Even if session is already completed, show summary
      navigation.navigate('ClinicalSummary', { consultationId });
    } finally {
      setCompleting(false);
    }
  };

  const handleVoiceToggle = async () => {
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <Header
        title="Clinical Interview"
        subtitle={`Language: ${activeLang}`}
        onBack={() => navigation.goBack()}
        rightAction={
          <TouchableOpacity
            onPress={() => navigation.navigate('DocumentUpload', { consultationId })}
            style={styles.skipBtn}
          >
            <Text style={styles.skipBtnText}>Docs →</Text>
          </TouchableOpacity>
        }
      />
      <StepIndicator currentStep={4} />

      {/* Global Emergency Alert Banner if detected */}
      {triageAlert && (
        <View style={{ paddingHorizontal: spacing.md }}>
          <EmergencyBanner
            triageResult={triageAlert}
            onDismiss={() => setTriageAlert(null)}
          />
        </View>
      )}

      {loadingSession ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Connecting to clinical interview engine...</Text>
        </View>
      ) : (
        <>
          <ScrollView
            ref={scrollViewRef}
            contentContainerStyle={styles.messagesContainer}
            keyboardShouldPersistTaps="handled"
          >
            <View style={styles.introCard}>
              <Ionicons name="information-circle-outline" size={20} color={colors.primary} />
              <Text style={styles.introText}>
                Please answer each question as accurately as you can. Your answers help your physician
                understand your symptoms and clinical history.
              </Text>
            </View>

            {messages.map((msg, idx) => {
              const isAssistant = msg.role === 'assistant' || msg.role === 'ai' || msg.role === 'system';
              return (
                <View
                  key={msg.id || idx}
                  style={[
                    styles.messageBubble,
                    isAssistant ? styles.assistantBubble : styles.patientBubble,
                  ]}
                >
                  <View style={styles.senderRow}>
                    <Ionicons
                      name={isAssistant ? 'sparkles' : 'person'}
                      size={14}
                      color={isAssistant ? colors.primary : colors.onPrimary}
                    />
                    <Text
                      style={[
                        styles.senderName,
                        isAssistant ? styles.assistantSenderText : styles.patientSenderText,
                      ]}
                    >
                      {isAssistant ? 'Clinova AI Intake' : 'You'}
                    </Text>
                  </View>
                  <Text
                    style={[
                      styles.messageText,
                      isAssistant ? styles.assistantMessageText : styles.patientMessageText,
                    ]}
                  >
                    {msg.content}
                  </Text>
                </View>
              );
            })}

            {sending && (
              <View style={[styles.messageBubble, styles.assistantBubble, styles.thinkingBubble]}>
                <ActivityIndicator size="small" color={colors.primary} />
                <Text style={styles.thinkingText}>Clinova AI is analyzing your response...</Text>
              </View>
            )}

            {isCompleted && (
              <Card style={styles.completedNotice}>
                <Ionicons name="checkmark-circle" size={28} color={colors.primary} />
                <Text style={styles.completedTitle}>Intake Questions Completed</Text>
                <Text style={styles.completedSubtitle}>
                  You have answered the primary intake questions. Next, upload any medical documents,
                  prescriptions, or lab reports you have.
                </Text>
                <Button
                  title="Proceed to Medical Documents"
                  onPress={() => navigation.navigate('DocumentUpload', { consultationId })}
                  style={{ marginTop: spacing.sm }}
                />
              </Card>
            )}
          </ScrollView>

          {/* Voice Input & Error Status Display */}
          {(voiceError || error) && (
            <View style={styles.errorNotice}>
              <Text style={styles.errorNoticeText}>{voiceError || error}</Text>
            </View>
          )}

          {isRecording && (
            <View style={styles.recordingIndicator}>
              <View style={styles.recordingDot} />
              <Text style={styles.recordingText}>Listening... Speak clearly into microphone</Text>
              <TouchableOpacity onPress={cancelRecording} style={styles.cancelRecordBtn}>
                <Text style={styles.cancelRecordText}>Cancel</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Input and Controls Bar */}
          <View style={styles.inputBar}>
            <TouchableOpacity
              activeOpacity={0.7}
              onPress={handleVoiceToggle}
              style={[styles.micBtn, isRecording && styles.micBtnActive]}
            >
              <Ionicons
                name={isRecording ? 'stop' : 'mic'}
                size={22}
                color={isRecording ? colors.onError : colors.primary}
              />
            </TouchableOpacity>

            <Input
              placeholder={isRecording ? 'Listening...' : 'Type your answer here...'}
              value={inputText}
              onChangeText={setInputText}
              containerStyle={styles.inputFieldContainer}
              style={styles.inputField}
              editable={!sending && !isRecording}
              onSubmitEditing={handleSendMessage}
              returnKeyType="send"
            />

            <TouchableOpacity
              activeOpacity={0.7}
              onPress={handleSendMessage}
              disabled={!inputText.trim() || sending}
              style={[
                styles.sendBtn,
                (!inputText.trim() || sending) && styles.sendBtnDisabled,
              ]}
            >
              <Ionicons name="send" size={18} color={colors.onPrimary} />
            </TouchableOpacity>
          </View>
        </>
      )}
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  skipBtn: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    backgroundColor: colors.surfaceContainer,
    borderRadius: borderRadius.sm,
  },
  skipBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primary,
  },
  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  loadingText: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  messagesContainer: {
    padding: spacing.md,
    paddingBottom: spacing.lg,
  },
  introCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.sm + 2,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  introText: {
    fontSize: 12,
    color: colors.onSurfaceVariant,
    marginLeft: spacing.xs + 2,
    flex: 1,
    lineHeight: 16,
  },
  messageBubble: {
    maxWidth: '85%',
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.md,
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: colors.surfaceContainerLowest,
    borderWidth: 1,
    borderColor: colors.border,
    borderBottomLeftRadius: 4,
  },
  patientBubble: {
    alignSelf: 'flex-end',
    backgroundColor: colors.primary,
    borderBottomRightRadius: 4,
  },
  senderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  senderName: {
    fontSize: 11,
    fontWeight: '700',
    marginLeft: 4,
  },
  assistantSenderText: {
    color: colors.primary,
  },
  patientSenderText: {
    color: colors.onPrimary,
  },
  messageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  assistantMessageText: {
    color: colors.onSurface,
  },
  patientMessageText: {
    color: colors.onPrimary,
  },
  thinkingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  thinkingText: {
    fontSize: 13,
    color: colors.textSecondary,
    fontStyle: 'italic',
    marginLeft: spacing.sm,
  },
  completedNotice: {
    alignItems: 'center',
    padding: spacing.lg,
    marginTop: spacing.md,
    backgroundColor: colors.surfaceContainerLow,
  },
  completedTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.onSurface,
    marginTop: spacing.xs,
  },
  completedSubtitle: {
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: 'center',
    marginVertical: spacing.xs,
    lineHeight: 16,
  },
  errorNotice: {
    backgroundColor: colors.errorContainer,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
  errorNoticeText: {
    color: colors.error,
    fontSize: 12,
    fontWeight: '500',
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
  },
  recordingDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.triageRed,
    marginRight: spacing.xs,
  },
  recordingText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.triageRed,
    flex: 1,
  },
  cancelRecordBtn: {
    paddingHorizontal: spacing.xs,
  },
  cancelRecordText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surfaceContainerLowest,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  micBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.secondaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
  },
  micBtnActive: {
    backgroundColor: colors.triageRed,
  },
  inputFieldContainer: {
    flex: 1,
    marginBottom: 0,
  },
  inputField: {
    height: 44,
    borderRadius: borderRadius.full,
    paddingHorizontal: spacing.md,
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.sm,
  },
  sendBtnDisabled: {
    backgroundColor: colors.disabled,
  },
});

export default InterviewScreen;
