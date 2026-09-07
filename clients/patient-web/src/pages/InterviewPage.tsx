import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import ProgressSteps from '../components/ProgressSteps';
import VoiceInput from '../components/VoiceInput';
import EmergencyOverlay from '../components/EmergencyOverlay';
import { usePatient } from '../context/PatientContext';
import { aiApi, triageApi } from '../api';
import { AIMessage, TriageResult } from '../types';
import {
  Send,
  Bot,
  User,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ChevronRight,
} from 'lucide-react';

export const InterviewPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    patient,
    activeConsultation,
    activeSession,
    language,
    triageAlert,
    setTriageAlert,
  } = usePatient();

  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [currentStepLabel, setCurrentStepLabel] = useState<string>('Clinical Intake');
  const [currentOptions, setCurrentOptions] = useState<string[]>([]);
  const [error, setError] = useState('');

  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Protect route
  useEffect(() => {
    if (!patient || !activeConsultation || !activeSession) {
      navigate('/identify');
    }
  }, [patient, activeConsultation, activeSession, navigate]);

  // Scroll to bottom whenever messages update
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSubmitting]);

  // Load message history on mount
  useEffect(() => {
    async function loadHistory() {
      if (!activeSession) return;
      try {
        const res = await aiApi.listMessages(activeSession.id);
        if (res.items && res.items.length > 0) {
          setMessages(res.items);
          const lastMsg = res.items[res.items.length - 1];
          if (lastMsg.role !== 'patient') {
            if (lastMsg.options) setCurrentOptions(lastMsg.options);
            if (lastMsg.current_step_label) setCurrentStepLabel(lastMsg.current_step_label);
            if (lastMsg.is_complete) setIsComplete(true);
          }
        }
      } catch (err) {
        console.error('Failed to load message history:', err);
      }
    }
    loadHistory();
  }, [activeSession]);

  // Send message handler with double-submit defense
  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || isSubmitting || !activeSession || !activeConsultation) return;

    setIsSubmitting(true);
    setError('');

    // Optimistically add patient message to UI
    const optimisticPatientMsg: AIMessage = {
      id: `temp-${Date.now()}`,
      session_id: activeSession.id,
      role: 'patient',
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimisticPatientMsg]);
    setInputText('');
    setCurrentOptions([]);

    try {
      // 1. Post patient response to AI Engine
      const aiResponse = await aiApi.sendMessage(activeSession.id, text);

      // 2. Add AI response to conversation
      const newAIMessage: AIMessage = {
        id: aiResponse.id,
        session_id: aiResponse.session_id,
        role: aiResponse.role,
        content: aiResponse.content,
        step: aiResponse.step,
        current_step_label: aiResponse.current_step_label,
        options: aiResponse.options,
        is_complete: aiResponse.is_complete,
        created_at: aiResponse.created_at || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, newAIMessage]);

      if (aiResponse.current_step_label) {
        setCurrentStepLabel(aiResponse.current_step_label);
      }
      if (aiResponse.options && aiResponse.options.length > 0) {
        setCurrentOptions(aiResponse.options);
      }
      if (aiResponse.is_complete) {
        setIsComplete(true);
      }

      // 3. Check triage state for potential red flags
      try {
        const triage = await triageApi.getTriageResult(activeConsultation.id);
        if (triage && (triage.priority === 'red' || triage.priority === 'orange')) {
          setTriageAlert(triage);
        }
      } catch {
        // Non-blocking if triage evaluation endpoint is idle
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to send message. Please try again.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsSubmitting(false);
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleVoiceTranscript = (voiceText: string) => {
    setInputText((prev) => (prev ? `${prev} ${voiceText}` : voiceText));
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Navbar />

      {/* Emergency Overlay if Red Flag Triage Triggered */}
      <EmergencyOverlay
        triage={triageAlert}
        onDismiss={() => setTriageAlert(null)}
      />

      <main className="max-w-3xl w-full mx-auto px-4 py-6 flex-1 flex flex-col">
        <ProgressSteps currentStepIndex={3} />

        {/* Chat Card */}
        <div className="card-elevated flex flex-col flex-1 min-h-[550px] max-h-[78vh] bg-surface-container-lowest overflow-hidden border border-outline-variant/30">
          {/* Chat Header Bar */}
          <div className="px-5 py-3.5 bg-surface-container-low border-b border-outline-variant/30 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary text-on-primary flex items-center justify-center shadow-xs">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-on-surface">Clinova AI Interview</h2>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-secondary-container/50 text-secondary text-[10px] font-bold">
                    <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
                    LIVE
                  </span>
                </div>
                <p className="text-xs text-on-surface-variant font-medium">
                  {currentStepLabel} • {language}
                </p>
              </div>
            </div>

            {isComplete && (
              <button
                onClick={() => navigate('/upload')}
                className="px-3.5 py-1.5 rounded-xl bg-primary text-on-primary text-xs font-bold hover:bg-primary-container transition-all flex items-center gap-1.5 shadow-xs"
              >
                <span>Upload Documents</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            {messages.length === 0 && !isSubmitting && (
              <div className="flex flex-col items-center justify-center py-12 text-center text-on-surface-variant">
                <Sparkles className="w-8 h-8 text-primary/40 mb-2" />
                <p className="text-sm font-semibold">Starting your clinical intake...</p>
                <p className="text-xs text-outline mt-1">
                  Describe how you are feeling in the input box below or use the microphone.
                </p>
              </div>
            )}

            {messages.map((msg, idx) => {
              const isPatient = msg.role === 'patient';

              return (
                <div
                  key={msg.id || idx}
                  className={`flex items-start gap-2.5 ${
                    isPatient ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {!isPatient && (
                    <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-1">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[82%] sm:max-w-[75%] rounded-2xl p-4 text-sm leading-relaxed ${
                      isPatient
                        ? 'bg-primary text-on-primary rounded-tr-xs shadow-xs'
                        : 'bg-surface-container-low text-on-surface border border-outline-variant/30 rounded-tl-xs shadow-xs'
                    }`}
                  >
                    {!isPatient && msg.current_step_label && (
                      <span className="text-[10px] font-bold uppercase tracking-wider text-primary block mb-1">
                        {msg.current_step_label}
                      </span>
                    )}

                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>

                  {isPatient && (
                    <div className="w-8 h-8 rounded-lg bg-secondary-container text-secondary flex items-center justify-center shrink-0 mt-1">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {/* AI Typing Indicator */}
            {isSubmitting && (
              <div className="flex items-start gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-1">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="p-4 rounded-2xl rounded-tl-xs bg-surface-container-low border border-outline-variant/30 text-on-surface-variant flex items-center gap-2">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-2 h-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-2 h-2 rounded-full bg-primary animate-bounce" />
                  </div>
                  <span className="text-xs font-semibold text-primary ml-1">
                    AI analyzing & framing response...
                  </span>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Quick Option Chips */}
          {currentOptions.length > 0 && !isComplete && !isSubmitting && (
            <div className="px-4 py-2 bg-surface-container-low/40 border-t border-outline-variant/20 flex flex-wrap gap-1.5">
              {currentOptions.map((opt, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSendMessage(opt)}
                  className="px-3 py-1.5 rounded-full bg-surface-container-lowest text-primary text-xs font-bold border border-primary/40 hover:bg-primary hover:text-on-primary shadow-xs transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <span>{opt}</span>
                  <ChevronRight className="w-3 h-3" />
                </button>
              ))}
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="px-4 py-2 bg-error-container/60 text-on-error-container text-xs flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5 text-error shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Input & Voice Controls */}
          <div className="p-3 sm:p-4 bg-surface-container-lowest border-t border-outline-variant/30">
            {isComplete ? (
              <div className="p-4 rounded-xl bg-secondary-container/30 border border-secondary-container text-center flex flex-col items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-secondary text-on-secondary flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-on-surface">
                    Clinical Intake Complete
                  </h3>
                  <p className="text-xs text-on-surface-variant mt-0.5">
                    Your symptoms and history have been recorded. Proceed to add any previous medical records.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => navigate('/upload')}
                  className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-primary text-on-primary font-bold text-xs shadow-md hover:bg-primary-container transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>Continue to Medical Documents</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-end gap-2 sm:gap-3">
                <div className="flex-1 relative">
                  <textarea
                    ref={textareaRef}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isSubmitting}
                    placeholder={`Type your response in ${language}... (Press Enter to send)`}
                    rows={2}
                    className="w-full p-3 rounded-xl bg-surface-container-low text-on-surface text-sm border border-outline-variant/40 resize-none focus:outline-none focus:bg-surface-container-lowest"
                  />
                </div>

                <VoiceInput
                  language={language}
                  onTranscript={handleVoiceTranscript}
                  disabled={isSubmitting}
                />

                <button
                  type="button"
                  onClick={() => handleSendMessage()}
                  disabled={!inputText.trim() || isSubmitting}
                  className="w-12 h-12 rounded-xl bg-primary text-on-primary flex items-center justify-center shadow-md hover:bg-primary-container transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
                  title="Send Message"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default InterviewPage;
