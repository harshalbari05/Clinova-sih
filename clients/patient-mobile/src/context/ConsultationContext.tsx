/**
 * Consultation & AI Intake Context for Clinova Patient Mobile
 * Coordinates hospital selection, consent, multilingual intake, AI messaging, and triage state.
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  Hospital,
  Consultation,
  AISession,
  AIMessage,
  TriageResult,
} from '../types';
import { api } from '../services/api';
import { getSecureItem, setSecureItem, STORAGE_KEYS } from '../services/storage';

interface ConsultationContextType {
  hospitals: Hospital[];
  selectedHospital: Hospital | null;
  activeConsultation: Consultation | null;
  consultation: Consultation | null;
  consentGiven: boolean;
  selectedLanguage: 'en' | 'hi' | 'mr';
  language: 'en' | 'hi' | 'mr';
  activeSession: AISession | null;
  messages: AIMessage[];
  isSendingMessage: boolean;
  latestTriage: TriageResult | null;
  isEmergencyModalVisible: boolean;
  loadHospitals: () => Promise<void>;
  selectHospital: (hospital: Hospital) => void;
  createConsultation: (chiefComplaint?: string, department?: string) => Promise<Consultation>;
  grantConsent: () => Promise<boolean>;
  setLanguage: (lang: 'en' | 'hi' | 'mr') => void;
  startAISession: () => Promise<AISession>;
  sendMessage: (text: string) => Promise<void>;
  checkTriage: () => Promise<TriageResult | null>;
  dismissEmergencyModal: () => void;
  resetConsultation: () => void;
  clearConsultation: () => void;
}

const ConsultationContext = createContext<ConsultationContextType | undefined>(undefined);

export const ConsultationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [selectedHospital, setSelectedHospital] = useState<Hospital | null>(null);
  const [activeConsultation, setActiveConsultation] = useState<Consultation | null>(null);
  const [consentGiven, setConsentGiven] = useState<boolean>(false);
  const [selectedLanguage, setSelectedLanguage] = useState<'en' | 'hi' | 'mr'>('en');
  const [activeSession, setActiveSession] = useState<AISession | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [isSendingMessage, setIsSendingMessage] = useState<boolean>(false);
  const [latestTriage, setLatestTriage] = useState<TriageResult | null>(null);
  const [isEmergencyModalVisible, setIsEmergencyModalVisible] = useState<boolean>(false);

  // Restore existing active consultation if saved
  useEffect(() => {
    const restoreActiveState = async () => {
      try {
        const savedConsultationId = await getSecureItem(STORAGE_KEYS.ACTIVE_CONSULTATION_ID);
        if (savedConsultationId) {
          const consultation = await api.getConsultation(savedConsultationId);
          setActiveConsultation(consultation);
        }
      } catch {
        // Safe ignore
      }
    };
    restoreActiveState();
  }, []);

  const loadHospitals = async () => {
    try {
      const list = await api.getHospitals();
      setHospitals(list);
      if (list.length > 0 && !selectedHospital) {
        setSelectedHospital(list[0]);
      }
    } catch {
      setHospitals([]);
    }
  };

  const selectHospital = (hospital: Hospital) => {
    setSelectedHospital(hospital);
  };

  const createConsultation = async (
    chiefComplaint?: string,
    department: string = 'General Medicine'
  ): Promise<Consultation> => {
    if (!selectedHospital && hospitals.length > 0) {
      setSelectedHospital(hospitals[0]);
    }
    const hospitalId = selectedHospital?.id || (hospitals[0]?.id ?? '');
    if (!hospitalId) {
      throw new Error('Please select a hospital to proceed with consultation.');
    }

    const consultation = await api.createConsultation({
      hospital_id: hospitalId,
      chief_complaint: chiefComplaint,
      department: department,
    });

    setActiveConsultation(consultation);
    await setSecureItem(STORAGE_KEYS.ACTIVE_CONSULTATION_ID, consultation.id);
    return consultation;
  };

  const grantConsent = async (): Promise<boolean> => {
    if (!activeConsultation) {
      throw new Error('No active consultation found to record consent.');
    }

    try {
      await api.recordConsent(activeConsultation.id);
      setConsentGiven(true);
      return true;
    } catch (err: any) {
      throw new Error(err.message || 'Consent could not be verified by hospital server.');
    }
  };

  const setLanguage = (lang: 'en' | 'hi' | 'mr') => {
    setSelectedLanguage(lang);
    setSecureItem(STORAGE_KEYS.ACTIVE_LANGUAGE, lang).catch(() => {});
  };

  const startAISession = async (): Promise<AISession> => {
    if (!activeConsultation) {
      throw new Error('Consultation must be created before starting AI intake.');
    }
    if (!consentGiven) {
      throw new Error('Patient consent is required before clinical intake begins.');
    }

    const session = await api.createAISession(activeConsultation.id, selectedLanguage);
    setActiveSession(session);

    // Initial greeting from backend or initial message list
    try {
      const initialMsgs = await api.getAIMessages(session.id);
      if (initialMsgs && initialMsgs.length > 0) {
        setMessages(initialMsgs);
      } else {
        const defaultGreeting =
          selectedLanguage === 'hi'
            ? 'नमस्ते, मैं क्लीनोवा क्लिनिकल असिस्टेंट हूँ। आज आपको क्या परेशानी महसूस हो रही है?'
            : selectedLanguage === 'mr'
            ? 'नमस्कार, मी क्लिनोव्हा क्लिनिकल सहाय्यक आहे. आज तुम्हाला काय त्रास जाणवत आहे?'
            : 'Hello, I am your Clinova Clinical Assistant. What brings you to the clinic today?';

        setMessages([
          {
            id: 'init-1',
            session_id: session.id,
            role: 'assistant',
            content: defaultGreeting,
            step: 'chief_complaint',
          },
        ]);
      }
    } catch {
      // Safe fallback message
    }

    return session;
  };

  const sendMessage = async (text: string): Promise<void> => {
    if (!activeSession) {
      throw new Error('No active AI session found.');
    }
    const cleanText = text.trim();
    if (!cleanText) return;

    // Optimistic patient message
    const tempPatientMsg: AIMessage = {
      id: `temp-${Date.now()}`,
      session_id: activeSession.id,
      role: 'patient',
      content: cleanText,
    };

    setMessages((prev) => [...prev, tempPatientMsg]);
    setIsSendingMessage(true);

    try {
      const response = await api.sendAIMessage(activeSession.id, cleanText);

      const aiMsg: AIMessage = {
        id: `ai-${Date.now()}`,
        session_id: activeSession.id,
        role: 'assistant',
        content: response.response,
        step: response.current_step,
        options: response.options,
        is_complete: response.is_complete,
      };

      setMessages((prev) => [...prev, aiMsg]);

      // Automatically evaluate triage in background after message exchange
      if (activeConsultation) {
        checkTriage().catch(() => {});
      }
    } finally {
      setIsSendingMessage(false);
    }
  };

  const checkTriage = async (): Promise<TriageResult | null> => {
    if (!activeConsultation) return null;
    try {
      const result = await api.getTriage(activeConsultation.id);
      setLatestTriage(result);

      // Trigger emergency modal if red-flag or EMERGENCY/URGENT priority detected
      const isUrgentOrEmergency =
        result.is_red_flag ||
        result.priority === 'red' ||
        result.priority === 'EMERGENCY' ||
        result.requires_immediate_escalation;

      if (isUrgentOrEmergency) {
        setIsEmergencyModalVisible(true);
      }
      return result;
    } catch {
      return null;
    }
  };

  const dismissEmergencyModal = () => {
    setIsEmergencyModalVisible(false);
  };

  const resetConsultation = () => {
    setActiveConsultation(null);
    setActiveSession(null);
    setConsentGiven(false);
    setMessages([]);
    setLatestTriage(null);
    setIsEmergencyModalVisible(false);
  };

  return (
    <ConsultationContext.Provider
      value={{
        hospitals,
        selectedHospital,
        activeConsultation,
        consultation: activeConsultation,
        consentGiven,
        selectedLanguage,
        language: selectedLanguage,
        activeSession,
        messages,
        isSendingMessage,
        latestTriage,
        isEmergencyModalVisible,
        loadHospitals,
        selectHospital,
        createConsultation,
        grantConsent,
        setLanguage,
        startAISession,
        sendMessage,
        checkTriage,
        dismissEmergencyModal,
        resetConsultation,
        clearConsultation: resetConsultation,
      }}
    >
      {children}
    </ConsultationContext.Provider>
  );
};

export const useConsultation = (): ConsultationContextType => {
  const context = useContext(ConsultationContext);
  if (!context) {
    throw new Error('useConsultation must be used within a ConsultationProvider');
  }
  return context;
};
