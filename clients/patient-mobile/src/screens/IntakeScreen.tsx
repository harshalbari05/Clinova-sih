/**
 * Mobile AI Medical Intake & Clinical History Screen
 * Faithfully matches clinova_patient_medical_history design with real backend AI interview integration.
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { colors, typography, spacing, borderRadius, shadows } from '../constants/theme';
import { Header } from '../components/common/Header';
import { Stepper, STEP_TITLES } from '../components/common/Stepper';
import { Badge } from '../components/common/Badge';
import { VoiceModal } from '../components/voice/VoiceModal';
import { EmergencyModal } from '../components/emergency/EmergencyModal';
import { useAuth } from '../context/AuthContext';
import { useConsultation } from '../context/ConsultationContext';

interface IntakeScreenProps {
  navigation?: any;
  onBack?: () => void;
  onProceedToDocuments?: () => void;
  onProceedToSummary?: () => void;
  onFinishIntake?: () => void;
  onNavigateToDocuments?: () => void;
  onNavigateToTimeline?: () => void;
}

export const IntakeScreen: React.FC<IntakeScreenProps> = ({
  navigation,
  onBack,
  onProceedToDocuments,
  onProceedToSummary,
  onFinishIntake,
  onNavigateToDocuments,
  onNavigateToTimeline,
}) => {
  const handleBack = onBack || (() => navigation?.goBack?.());
  const { patient } = useAuth();
  const {
    hospitals,
    selectedHospital,
    selectHospital,
    activeConsultation,
    createConsultation,
    consentGiven,
    grantConsent,
    selectedLanguage,
    setLanguage,
    activeSession,
    startAISession,
    messages,
    sendMessage,
    isSendingMessage,
    latestTriage,
    isEmergencyModalVisible,
    dismissEmergencyModal,
    checkTriage,
  } = useConsultation();

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isVoiceModalVisible, setIsVoiceModalVisible] = useState<boolean>(false);
  const [inputText, setInputText] = useState<string>('');
  const [isStartingSession, setIsStartingSession] = useState<boolean>(false);
  const [isGrantingConsent, setIsGrantingConsent] = useState<boolean>(false);

  // Intake State Fields
  const [fullName, setFullName] = useState<string>(patient?.full_name || 'Rahul Sharma');
  const [gender, setGender] = useState<string>('Male');
  const [bloodGroup, setBloodGroup] = useState<string>('O+');
  const [chiefComplaint, setChiefComplaint] = useState<string>(
    'I have had a severe throbbing headache and mild fever since yesterday night, along with general body weakness.'
  );
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([
    'Fever',
    'Headache',
    'Body Ache',
    'Fatigue',
  ]);
  const [hasPastConditions, setHasPastConditions] = useState<boolean>(true);
  const [conditions, setConditions] = useState<string[]>(['High Blood Pressure (BP / Hypertension)']);
  const [takingMeds, setTakingMeds] = useState<boolean>(true);
  const [medsList, setMedsList] = useState<string[]>(['Amlodipine 5mg (Once daily)']);
  const [allergyText, setAllergyText] = useState<string>('Penicillin / Amoxicillin reaction');
  const [hasSurgery, setHasSurgery] = useState<boolean>(true);
  const [surgeryName, setSurgeryName] = useState<string>('Appendectomy (2019)');
  const [familyConditions, setFamilyConditions] = useState<string[]>(['Diabetes']);

  const scrollViewRef = useRef<ScrollView>(null);

  // Initialize consultation if needed
  useEffect(() => {
    if (!activeConsultation && hospitals.length > 0) {
      createConsultation(chiefComplaint, 'General Medicine').catch(() => {});
    }
  }, [hospitals]);

  const handleGrantConsent = async () => {
    try {
      setIsGrantingConsent(true);
      await grantConsent();
    } catch (err: any) {
      Alert.alert('Consent Notice', err.message);
    } finally {
      setIsGrantingConsent(false);
    }
  };

  const handleStartAI = async () => {
    try {
      setIsStartingSession(true);
      await startAISession();
    } catch (err: any) {
      Alert.alert('Intake Initialization', err.message);
    } finally {
      setIsStartingSession(false);
    }
  };

  const handleSend = async () => {
    const textToSend = inputText.trim();
    if (!textToSend || isSendingMessage) return;
    setInputText('');
    try {
      await sendMessage(textToSend);
      scrollViewRef.current?.scrollToEnd({ animated: true });
    } catch (err: any) {
      Alert.alert('Unable to Send', err.message);
    }
  };

  const handleVoiceTranscript = (transcript: string) => {
    if (activeSession) {
      setInputText(transcript);
    } else {
      setChiefComplaint(transcript);
    }
  };

  const toggleSymptom = (name: string) => {
    setSelectedSymptoms((prev) =>
      prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name]
    );
  };

  const toggleCondition = (cond: string) => {
    setConditions((prev) =>
      prev.includes(cond) ? prev.filter((c) => c !== cond) : [...prev, cond]
    );
  };

  const quickPhrases = [
    '+ Severe headache',
    '+ Persistent dry cough',
    '+ Chest discomfort',
    '+ Stomach ache',
    '+ High fever',
  ];

  const appendPhrase = (phrase: string) => {
    const clean = phrase.replace(/^\+\s*/, '');
    setChiefComplaint((prev) => (prev ? `${prev}, ${clean}` : clean));
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <Header
        title="CLINOVA"
        subtitle="Medical Intake"
        showBack
        onBack={handleBack}
        rightAction={{
          label: 'Save & Exit',
          onPress: handleBack,
        }}
      />

      <ScrollView
        ref={scrollViewRef}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Context Banner */}
        <View style={styles.bannerBox}>
          <View style={styles.bannerRow}>
            <View style={styles.doctorBadge}>
              <View style={styles.doctorDot} />
              <Text style={styles.doctorBadgeText}>
                {selectedHospital?.name || 'City Hospital OPD'} • General Medicine
              </Text>
            </View>
            <Text style={styles.sessionText}>Session #408</Text>
          </View>
          <Text style={styles.bannerTitle}>Clinical Pre-Consultation</Text>
          <Text style={styles.bannerDesc}>
            This structured record helps your physician prepare appropriate care before you enter the examination room.
          </Text>
        </View>

        {/* Consent Section (Strict Gating) */}
        {!consentGiven && (
          <View style={styles.consentCard}>
            <View style={styles.consentHeader}>
              <Text style={styles.shieldEmoji}>🛡️</Text>
              <View>
                <Text style={styles.consentTitle}>Consent for AI-Assisted Clinical Intake</Text>
                <Text style={styles.consentSubtitle}>Mandatory patient authorization</Text>
              </View>
            </View>

            <Text style={styles.consentBody}>
              I consent to share my health history with Clinova to help my doctor review symptoms and
              check safety red-flags. All clinical data is securely transmitted to the hospital EMR.
            </Text>

            <TouchableOpacity
              onPress={handleGrantConsent}
              disabled={isGrantingConsent}
              style={styles.consentButton}
            >
              {isGrantingConsent ? (
                <ActivityIndicator color={colors.textLight} />
              ) : (
                <Text style={styles.consentButtonText}>I Consent & Agree →</Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        {/* Multilingual Selector */}
        <View style={styles.langSelectorRow}>
          <Text style={styles.langLabel}>Language / भाषा:</Text>
          <View style={styles.langPills}>
            <TouchableOpacity
              onPress={() => setLanguage('en')}
              style={[styles.langPill, selectedLanguage === 'en' && styles.langPillActive]}
            >
              <Text style={[styles.langText, selectedLanguage === 'en' && styles.langTextActive]}>
                English
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => setLanguage('hi')}
              style={[styles.langPill, selectedLanguage === 'hi' && styles.langPillActive]}
            >
              <Text style={[styles.langText, selectedLanguage === 'hi' && styles.langTextActive]}>
                हिंदी
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => setLanguage('mr')}
              style={[styles.langPill, selectedLanguage === 'mr' && styles.langPillActive]}
            >
              <Text style={[styles.langText, selectedLanguage === 'mr' && styles.langTextActive]}>
                मराठी
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 7-Step Stepper */}
        <Stepper
          currentStep={currentStep}
          totalSteps={7}
          onStepPress={(step) => setCurrentStep(step)}
        />

        {/* ================= STEP 1: ABOUT YOU ================= */}
        {currentStep === 1 && (
          <View style={styles.stepCard}>
            <View style={styles.stepCardHeader}>
              <View style={styles.stepIconBox}>
                <Text style={styles.stepIconEmoji}>🪪</Text>
              </View>
              <View>
                <Text style={styles.stepTitle}>About You</Text>
                <Text style={styles.stepSubtitle}>Confirm your basic patient details</Text>
              </View>
            </View>

            <Text style={styles.fieldLabel}>Full Legal Name</Text>
            <TextInput style={styles.input} value={fullName} onChangeText={setFullName} />

            <Text style={styles.fieldLabel}>Biological Sex / Gender</Text>
            <View style={styles.genderRow}>
              {['Male', 'Female', 'Other'].map((g) => (
                <TouchableOpacity
                  key={g}
                  onPress={() => setGender(g)}
                  style={[styles.choicePill, gender === g && styles.choicePillActive]}
                >
                  <Text style={[styles.choiceText, gender === g && styles.choiceTextActive]}>
                    {g}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.fieldLabel}>Blood Group</Text>
            <View style={styles.bloodGrid}>
              {['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-'].map((bg) => (
                <TouchableOpacity
                  key={bg}
                  onPress={() => setBloodGroup(bg)}
                  style={[styles.bloodPill, bloodGroup === bg && styles.bloodPillActive]}
                >
                  <Text style={[styles.bloodText, bloodGroup === bg && styles.bloodTextActive]}>
                    {bg}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity onPress={() => setCurrentStep(2)} style={styles.nextStepBtn}>
              <Text style={styles.nextStepBtnText}>Continue to Problem →</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* ================= STEP 2: CURRENT PROBLEM & VOICE ================= */}
        {currentStep === 2 && (
          <View style={styles.stepCard}>
            <View style={styles.stepCardHeader}>
              <View style={[styles.stepIconBox, { backgroundColor: colors.primaryLight }]}>
                <Text style={styles.stepIconEmoji}>💬</Text>
              </View>
              <View>
                <Text style={styles.stepTitle}>What brings you in today?</Text>
                <Text style={styles.stepSubtitle}>Explain in simple words or speak naturally</Text>
              </View>
            </View>

            {/* Voice Input Callout Button */}
            <TouchableOpacity
              onPress={() => setIsVoiceModalVisible(true)}
              style={styles.voiceCalloutButton}
              accessibilityRole="button"
            >
              <View style={styles.voiceCalloutLeft}>
                <View style={styles.voiceMicCircle}>
                  <Text style={styles.voiceMicIcon}>🎙️</Text>
                </View>
                <View>
                  <Text style={styles.voiceCalloutTitle}>Tap here to speak instead</Text>
                  <Text style={styles.voiceCalloutSubtitle}>
                    Clinova AI transcribes symptoms in Hindi, English & Marathi
                  </Text>
                </View>
              </View>
              <Text style={styles.chevron}>→</Text>
            </TouchableOpacity>

            <Text style={styles.fieldLabel}>Primary Complaint (Chief Complaint)</Text>
            <TextInput
              style={styles.textArea}
              multiline
              numberOfLines={4}
              value={chiefComplaint}
              onChangeText={setChiefComplaint}
              placeholder="Describe what you feel..."
              placeholderTextColor={colors.textSubtle}
            />

            <Text style={styles.quickPhraseTitle}>Tap to add common phrases:</Text>
            <View style={styles.quickPhraseRow}>
              {quickPhrases.map((phrase, i) => (
                <TouchableOpacity
                  key={i}
                  onPress={() => appendPhrase(phrase)}
                  style={styles.phraseChip}
                >
                  <Text style={styles.phraseText}>{phrase}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.stepNavRow}>
              <TouchableOpacity onPress={() => setCurrentStep(1)} style={styles.backStepBtn}>
                <Text style={styles.backStepBtnText}>← Back</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setCurrentStep(3)} style={styles.forwardStepBtn}>
                <Text style={styles.forwardStepBtnText}>Continue to Symptoms →</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ================= STEP 3: SYMPTOMS SELECTION ================= */}
        {currentStep === 3 && (
          <View style={styles.stepCard}>
            <View style={styles.stepCardHeader}>
              <View style={[styles.stepIconBox, { backgroundColor: '#FEF3C7' }]}>
                <Text style={styles.stepIconEmoji}>🌡️</Text>
              </View>
              <View>
                <Text style={styles.stepTitle}>What symptoms do you have?</Text>
                <Text style={styles.stepSubtitle}>Tap any box that describes what you feel</Text>
              </View>
            </View>

            <View style={styles.symptomsGrid}>
              {[
                { name: 'Fever', emoji: '🌡️', desc: 'High temp' },
                { name: 'Headache', emoji: '🤕', desc: 'Throbbing' },
                { name: 'Cough', emoji: '🗣️', desc: 'Dry or wet' },
                { name: 'Cold', emoji: '🤧', desc: 'Runny nose' },
                { name: 'Body Ache', emoji: '⚡', desc: 'Soreness' },
                { name: 'Nausea', emoji: '🤢', desc: 'Vomiting' },
                { name: 'Stomach', emoji: '🫄', desc: 'Cramps' },
                { name: 'Fatigue', emoji: '🥱', desc: 'Weakness' },
                { name: 'Breathing', emoji: '🫁', desc: 'Short breath' },
                { name: 'Other', emoji: '➕', desc: 'Describe' },
              ].map((item) => {
                const isSelected = selectedSymptoms.includes(item.name);
                return (
                  <TouchableOpacity
                    key={item.name}
                    onPress={() => toggleSymptom(item.name)}
                    style={[styles.symptomCard, isSelected && styles.symptomCardActive]}
                  >
                    <Text style={styles.symptomEmoji}>{item.emoji}</Text>
                    <View style={styles.symptomTextCol}>
                      <Text style={[styles.symptomName, isSelected && styles.symptomNameActive]}>
                        {item.name}
                      </Text>
                      <Text style={styles.symptomDesc}>{item.desc}</Text>
                    </View>
                    <Text style={[styles.symptomCheck, isSelected && styles.symptomCheckActive]}>
                      {isSelected ? '✓' : '○'}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <View style={styles.stepNavRow}>
              <TouchableOpacity onPress={() => setCurrentStep(2)} style={styles.backStepBtn}>
                <Text style={styles.backStepBtnText}>← Back</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setCurrentStep(4)} style={styles.forwardStepBtn}>
                <Text style={styles.forwardStepBtnText}>Continue to History →</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ================= STEP 4: PAST HEALTH CONDITIONS ================= */}
        {currentStep === 4 && (
          <View style={styles.stepCard}>
            <View style={styles.stepCardHeader}>
              <View style={[styles.stepIconBox, { backgroundColor: '#E0F2FE' }]}>
                <Text style={styles.stepIconEmoji}>📜</Text>
              </View>
              <View>
                <Text style={styles.stepTitle}>Past Health Conditions</Text>
                <Text style={styles.stepSubtitle}>Do you have ongoing medical conditions?</Text>
              </View>
            </View>

            <View style={styles.toggleRow}>
              <TouchableOpacity
                onPress={() => setHasPastConditions(true)}
                style={[styles.toggleBtn, hasPastConditions && styles.toggleBtnActive]}
              >
                <Text style={[styles.toggleText, hasPastConditions && styles.toggleTextActive]}>
                  Yes, I have
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setHasPastConditions(false)}
                style={[styles.toggleBtn, !hasPastConditions && styles.toggleBtnActive]}
              >
                <Text style={[styles.toggleText, !hasPastConditions && styles.toggleTextActive]}>
                  No, None
                </Text>
              </TouchableOpacity>
            </View>

            {hasPastConditions && (
              <View style={styles.checklistColumn}>
                {[
                  'Diabetes (High Blood Sugar)',
                  'High Blood Pressure (BP / Hypertension)',
                  'Asthma / Wheezing',
                  'Heart Condition (Angina / Stent)',
                  'Thyroid Disorder',
                  'Kidney / Liver Condition',
                ].map((cond) => {
                  const isChecked = conditions.includes(cond);
                  return (
                    <TouchableOpacity
                      key={cond}
                      onPress={() => toggleCondition(cond)}
                      style={[styles.checkRow, isChecked && styles.checkRowActive]}
                    >
                      <Text style={[styles.checkText, isChecked && styles.checkTextActive]}>
                        {cond}
                      </Text>
                      <Text style={[styles.checkIcon, isChecked && styles.checkIconActive]}>
                        {isChecked ? '✓' : '○'}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}

            <View style={styles.safetyCallout}>
              <Text style={styles.safetyIcon}>🛡️</Text>
              <Text style={styles.safetyText}>
                <strong>Clinical Safety:</strong> Declaring conditions prevents adverse drug interactions.
              </Text>
            </View>

            <View style={styles.stepNavRow}>
              <TouchableOpacity onPress={() => setCurrentStep(3)} style={styles.backStepBtn}>
                <Text style={styles.backStepBtnText}>← Back</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setCurrentStep(5)} style={styles.forwardStepBtn}>
                <Text style={styles.forwardStepBtnText}>Continue to Meds →</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ================= STEP 5: MEDICINES & ALLERGIES ================= */}
        {currentStep === 5 && (
          <View style={styles.stepCard}>
            <View style={styles.stepCardHeader}>
              <View style={[styles.stepIconBox, { backgroundColor: '#FCE7F3' }]}>
                <Text style={styles.stepIconEmoji}>💊</Text>
              </View>
              <View>
                <Text style={styles.stepTitle}>Medicines & Allergies</Text>
                <Text style={styles.stepSubtitle}>Prescriptions you take and substances to avoid</Text>
              </View>
            </View>

            <Text style={styles.fieldLabel}>Current Medications</Text>
            {medsList.map((med, index) => (
              <View key={index} style={styles.medItemRow}>
                <Text style={styles.pillIcon}>💊</Text>
                <Text style={styles.medItemText}>{med}</Text>
              </View>
            ))}

            <View style={styles.allergyHeaderRow}>
              <Text style={styles.fieldLabel}>Known Drug Allergies</Text>
              <Badge label="Crucial for doctor" type="error" />
            </View>
            <TextInput
              style={styles.input}
              value={allergyText}
              onChangeText={setAllergyText}
              placeholder="e.g. Penicillin, Sulfa drugs..."
              placeholderTextColor={colors.textSubtle}
            />

            <View style={styles.stepNavRow}>
              <TouchableOpacity onPress={() => setCurrentStep(4)} style={styles.backStepBtn}>
                <Text style={styles.backStepBtnText}>← Back</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setCurrentStep(6)} style={styles.forwardStepBtn}>
                <Text style={styles.forwardStepBtnText}>Continue to Surgeries →</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ================= STEP 6: SURGERIES & FAMILY ================= */}
        {currentStep === 6 && (
          <View style={styles.stepCard}>
            <View style={styles.stepCardHeader}>
              <View style={[styles.stepIconBox, { backgroundColor: '#EDE9FE' }]}>
                <Text style={styles.stepIconEmoji}>👨‍👩‍👧</Text>
              </View>
              <View>
                <Text style={styles.stepTitle}>Surgeries & Family History</Text>
                <Text style={styles.stepSubtitle}>Evaluates hereditary risks and past procedures</Text>
              </View>
            </View>

            <Text style={styles.fieldLabel}>Past Surgeries & Year</Text>
            <TextInput style={styles.input} value={surgeryName} onChangeText={setSurgeryName} />

            <Text style={styles.fieldLabel}>Family Medical History</Text>
            <View style={styles.familyChipsGrid}>
              {['Diabetes', 'Heart Condition', 'High BP', 'Thyroid'].map((fam) => {
                const isSelected = familyConditions.includes(fam);
                return (
                  <TouchableOpacity
                    key={fam}
                    onPress={() =>
                      setFamilyConditions((prev) =>
                        prev.includes(fam) ? prev.filter((f) => f !== fam) : [...prev, fam]
                      )
                    }
                    style={[styles.familyChip, isSelected && styles.familyChipActive]}
                  >
                    <Text style={[styles.familyText, isSelected && styles.familyTextActive]}>
                      {fam} {isSelected ? '✓' : ''}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <View style={styles.stepNavRow}>
              <TouchableOpacity onPress={() => setCurrentStep(5)} style={styles.backStepBtn}>
                <Text style={styles.backStepBtnText}>← Back</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setCurrentStep(7)} style={styles.forwardStepBtn}>
                <Text style={styles.forwardStepBtnText}>Review Summary →</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* ================= STEP 7: REVIEW & LIVE ADAPTIVE AI CHAT ================= */}
        {currentStep === 7 && (
          <View style={styles.stepCard}>
            <View style={styles.readyBanner}>
              <Text style={styles.readyEmoji}>✅</Text>
              <View style={styles.readyTextCol}>
                <Text style={styles.readyTitle}>All 6 Clinical Sections Completed</Text>
                <Text style={styles.readySubtitle}>
                  Connect directly with Clinova Adaptive AI to finalize intake.
                </Text>
              </View>
            </View>

            {/* Live AI Adaptive Chat Section */}
            {!activeSession ? (
              <View style={styles.aiStartBox}>
                <Text style={styles.aiStartTitle}>Interactive AI Interview</Text>
                <Text style={styles.aiStartDesc}>
                  Clinova Adaptive AI will ask clarifying questions about your symptoms to give your doctor high-fidelity clinical summaries.
                </Text>
                <TouchableOpacity
                  onPress={handleStartAI}
                  disabled={isStartingSession}
                  style={styles.startAiBtn}
                >
                  {isStartingSession ? (
                    <ActivityIndicator color={colors.textLight} />
                  ) : (
                    <Text style={styles.startAiBtnText}>Start Adaptive AI Interview →</Text>
                  )}
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.chatContainer}>
                <View style={styles.chatHeaderRow}>
                  <View style={styles.chatBadge}>
                    <View style={styles.chatDot} />
                    <Text style={styles.chatBadgeText}>Adaptive AI Active</Text>
                  </View>
                  <TouchableOpacity onPress={() => checkTriage()} style={styles.triageBtn}>
                    <Text style={styles.triageBtnText}>Check Triage Status</Text>
                  </TouchableOpacity>
                </View>

                {/* Messages List */}
                <View style={styles.messagesList}>
                  {messages.map((msg) => {
                    const isAssistant = msg.role === 'assistant' || msg.role === 'ai';
                    return (
                      <View
                        key={msg.id}
                        style={[
                          styles.messageBubble,
                          isAssistant ? styles.assistantBubble : styles.patientBubble,
                        ]}
                      >
                        <Text
                          style={[
                            styles.messageText,
                            isAssistant ? styles.assistantText : styles.patientText,
                          ]}
                        >
                          {msg.content}
                        </Text>
                      </View>
                    );
                  })}
                  {isSendingMessage && (
                    <View style={[styles.messageBubble, styles.assistantBubble]}>
                      <ActivityIndicator size="small" color={colors.primary} />
                    </View>
                  )}
                </View>

                {/* Chat Input Row */}
                <View style={styles.chatInputRow}>
                  <TouchableOpacity
                    onPress={() => setIsVoiceModalVisible(true)}
                    style={styles.micButton}
                  >
                    <Text style={styles.micIcon}>🎙️</Text>
                  </TouchableOpacity>

                  <TextInput
                    style={styles.chatInput}
                    placeholder="Type your response..."
                    placeholderTextColor={colors.textSubtle}
                    value={inputText}
                    onChangeText={setInputText}
                    onSubmitEditing={handleSend}
                  />

                  <TouchableOpacity
                    onPress={handleSend}
                    disabled={isSendingMessage || !inputText.trim()}
                    style={[
                      styles.sendButton,
                      (!inputText.trim() || isSendingMessage) && styles.sendButtonDisabled,
                    ]}
                  >
                    <Text style={styles.sendButtonText}>Send</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}

            {/* Step Navigation to Documents & Summary */}
            <View style={styles.finalActions}>
              <TouchableOpacity onPress={onProceedToDocuments} style={styles.proceedDocBtn}>
                <Text style={styles.proceedDocBtnText}>Add Medical Documents & Reports →</Text>
              </TouchableOpacity>

              <TouchableOpacity onPress={onProceedToSummary} style={styles.proceedSummaryBtn}>
                <Text style={styles.proceedSummaryBtnText}>View Clinical Summary →</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Voice Assistant Modal */}
      <VoiceModal
        visible={isVoiceModalVisible}
        language={selectedLanguage}
        onClose={() => setIsVoiceModalVisible(false)}
        onAcceptTranscript={handleVoiceTranscript}
      />

      {/* Triage Emergency Modal (Driven strictly by backend triage) */}
      <EmergencyModal
        visible={isEmergencyModalVisible}
        triage={latestTriage}
        onDismiss={dismissEmergencyModal}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: 60,
  },
  bannerBox: {
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.md,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  bannerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  doctorBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colors.secondaryContainer,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
  },
  doctorDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.secondary,
  },
  doctorBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.onSecondaryContainer,
  },
  sessionText: {
    fontSize: 11,
    color: colors.textMuted,
  },
  bannerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.textPrimary,
    marginTop: 4,
  },
  bannerDesc: {
    fontSize: 12,
    color: colors.textMuted,
    lineHeight: 16,
    marginTop: 2,
  },
  consentCard: {
    backgroundColor: '#FEF3C7',
    padding: spacing.md,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: '#FDE68A',
    marginBottom: spacing.md,
  },
  consentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: 6,
  },
  shieldEmoji: {
    fontSize: 20,
  },
  consentTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#78350F',
  },
  consentSubtitle: {
    fontSize: 11,
    color: '#92400E',
  },
  consentBody: {
    fontSize: 12,
    color: '#92400E',
    lineHeight: 16,
    marginBottom: spacing.sm,
  },
  consentButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm + 2,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  consentButtonText: {
    color: colors.textLight,
    fontSize: 12,
    fontWeight: '700',
  },
  langSelectorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
    paddingHorizontal: 4,
  },
  langLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  langPills: {
    flexDirection: 'row',
    gap: 6,
  },
  langPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: borderRadius.full,
    backgroundColor: colors.surfaceContainerLow,
    borderWidth: 1,
    borderColor: colors.border,
  },
  langPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  langText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textMuted,
  },
  langTextActive: {
    color: colors.textLight,
    fontWeight: '800',
  },
  stepCard: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.xxl,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    ...shadows.card,
  },
  stepCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  stepIconBox: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: colors.secondaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepIconEmoji: {
    fontSize: 22,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  stepSubtitle: {
    fontSize: 12,
    color: colors.textMuted,
  },
  fieldLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textSecondary,
    marginBottom: 6,
    marginTop: 8,
  },
  input: {
    minHeight: 46,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    paddingHorizontal: spacing.md,
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  genderRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  choicePill: {
    flex: 1,
    minHeight: 44,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
  },
  choicePillActive: {
    backgroundColor: colors.primary,
  },
  choiceText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.textMuted,
  },
  choiceTextActive: {
    color: colors.textLight,
  },
  bloodGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: spacing.lg,
  },
  bloodPill: {
    width: '23%',
    minHeight: 40,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
  },
  bloodPillActive: {
    backgroundColor: colors.secondaryContainer,
    borderWidth: 1,
    borderColor: colors.secondary,
  },
  bloodText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  bloodTextActive: {
    color: colors.onSecondaryContainer,
    fontWeight: '900',
  },
  nextStepBtn: {
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.md,
  },
  nextStepBtnText: {
    color: colors.textLight,
    fontSize: 14,
    fontWeight: '800',
  },
  voiceCalloutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.secondaryContainer,
    padding: spacing.md,
    borderRadius: borderRadius.xl,
    marginBottom: spacing.md,
  },
  voiceCalloutLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    flex: 1,
    paddingRight: spacing.sm,
  },
  voiceMicCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.secondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  voiceMicIcon: {
    fontSize: 18,
  },
  voiceCalloutTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.onSecondaryContainer,
  },
  voiceCalloutSubtitle: {
    fontSize: 11,
    color: colors.onSecondaryContainer,
    opacity: 0.85,
  },
  chevron: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.secondary,
  },
  textArea: {
    minHeight: 88,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.md,
    fontSize: 14,
    color: colors.textPrimary,
    lineHeight: 20,
    textAlignVertical: 'top',
  },
  quickPhraseTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textMuted,
    marginTop: spacing.md,
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  quickPhraseRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: spacing.md,
  },
  phraseChip: {
    backgroundColor: colors.surfaceContainerLow,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: borderRadius.md,
  },
  phraseText: {
    fontSize: 12,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  stepNavRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  backStepBtn: {
    flex: 1,
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backStepBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  forwardStepBtn: {
    flex: 2,
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  forwardStepBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.textLight,
  },
  symptomsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  symptomCard: {
    width: '48.5%',
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.sm + 2,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    borderWidth: 1,
    borderColor: colors.border,
  },
  symptomCardActive: {
    backgroundColor: colors.secondaryContainer,
    borderColor: colors.secondary,
  },
  symptomEmoji: {
    fontSize: 20,
    marginRight: 6,
  },
  symptomTextCol: {
    flex: 1,
  },
  symptomName: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  symptomNameActive: {
    color: colors.onSecondaryContainer,
  },
  symptomDesc: {
    fontSize: 10,
    color: colors.textMuted,
  },
  symptomCheck: {
    fontSize: 13,
    color: colors.textSubtle,
    marginLeft: 4,
  },
  symptomCheckActive: {
    color: colors.secondary,
    fontWeight: '900',
  },
  toggleRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  toggleBtn: {
    flex: 1,
    minHeight: 44,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    alignItems: 'center',
    justifyContent: 'center',
  },
  toggleBtnActive: {
    backgroundColor: colors.primary,
  },
  toggleText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.textMuted,
  },
  toggleTextActive: {
    color: colors.textLight,
  },
  checklistColumn: {
    gap: 6,
    marginBottom: spacing.md,
  },
  checkRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surfaceContainerLow,
  },
  checkRowActive: {
    backgroundColor: colors.secondaryContainer,
  },
  checkText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  checkTextActive: {
    color: colors.onSecondaryContainer,
    fontWeight: '700',
  },
  checkIcon: {
    fontSize: 14,
    color: colors.textSubtle,
  },
  checkIconActive: {
    color: colors.secondary,
    fontWeight: '900',
  },
  safetyCallout: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    padding: spacing.md,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.md,
    marginBottom: spacing.sm,
  },
  safetyIcon: {
    fontSize: 16,
  },
  safetyText: {
    fontSize: 12,
    color: colors.textSecondary,
    flex: 1,
    lineHeight: 16,
  },
  medItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    marginBottom: 6,
  },
  pillIcon: {
    fontSize: 16,
  },
  medItemText: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  allergyHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  familyChipsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: spacing.md,
  },
  familyChip: {
    backgroundColor: colors.surfaceContainerLow,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: borderRadius.md,
  },
  familyChipActive: {
    backgroundColor: colors.secondaryContainer,
  },
  familyText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  familyTextActive: {
    color: colors.onSecondaryContainer,
    fontWeight: '800',
  },
  readyBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.secondaryContainer,
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.md,
  },
  readyEmoji: {
    fontSize: 22,
  },
  readyTextCol: {
    flex: 1,
  },
  readyTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.onSecondaryContainer,
  },
  readySubtitle: {
    fontSize: 11,
    color: colors.onSecondaryContainer,
  },
  aiStartBox: {
    backgroundColor: colors.surfaceContainerLow,
    padding: spacing.lg,
    borderRadius: borderRadius.xl,
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  aiStartTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  aiStartDesc: {
    fontSize: 12,
    color: colors.textMuted,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: spacing.md,
  },
  startAiBtn: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.lg,
  },
  startAiBtnText: {
    color: colors.textLight,
    fontSize: 13,
    fontWeight: '800',
  },
  chatContainer: {
    marginBottom: spacing.md,
  },
  chatHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  chatBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  chatDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.emerald,
  },
  chatBadgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.primary,
  },
  triageBtn: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surfaceContainerLow,
  },
  triageBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textMuted,
  },
  messagesList: {
    gap: spacing.sm,
    marginBottom: spacing.md,
    minHeight: 160,
  },
  messageBubble: {
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    maxWidth: '85%',
  },
  assistantBubble: {
    backgroundColor: colors.surfaceContainerLow,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: colors.border,
  },
  patientBubble: {
    backgroundColor: colors.primary,
    alignSelf: 'flex-end',
  },
  messageText: {
    fontSize: 13,
    lineHeight: 18,
  },
  assistantText: {
    color: colors.textPrimary,
  },
  patientText: {
    color: colors.textLight,
  },
  chatInputRow: {
    flexDirection: 'row',
    gap: spacing.xs,
    alignItems: 'center',
  },
  micButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.secondaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
  },
  micIcon: {
    fontSize: 18,
  },
  chatInput: {
    flex: 1,
    minHeight: 44,
    backgroundColor: colors.surfaceContainerLow,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.md,
    fontSize: 14,
    color: colors.textPrimary,
  },
  sendButton: {
    minHeight: 44,
    paddingHorizontal: spacing.md,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  sendButtonText: {
    color: colors.textLight,
    fontSize: 13,
    fontWeight: '700',
  },
  finalActions: {
    marginTop: spacing.lg,
    gap: spacing.sm,
  },
  proceedDocBtn: {
    minHeight: 48,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  proceedDocBtnText: {
    color: colors.textLight,
    fontSize: 13,
    fontWeight: '800',
  },
  proceedSummaryBtn: {
    minHeight: 44,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.surfaceContainerLow,
    borderWidth: 1,
    borderColor: colors.primaryBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },
  proceedSummaryBtnText: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: '700',
  },
});
