import React from 'react';
import { Mic, MicOff, AlertCircle } from 'lucide-react';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';

interface VoiceInputProps {
  language: string;
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({ language, onTranscript, disabled }) => {
  const { isSupported, isListening, interimTranscript, startListening, stopListening } =
    useSpeechRecognition({
      language,
      onFinalTranscript: (text) => {
        if (text.trim()) {
          onTranscript(text.trim());
        }
      },
    });

  if (!isSupported) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-on-surface-variant bg-surface-container-low px-2 py-1 rounded-lg">
        <AlertCircle className="w-3.5 h-3.5 text-outline" />
        <span className="text-[11px]">Speech-to-text not supported on this browser</span>
      </div>
    );
  }

  const toggleListening = () => {
    if (disabled) return;
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        type="button"
        onClick={toggleListening}
        disabled={disabled}
        className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-200 ${
          isListening
            ? 'bg-error text-on-error shadow-emergency mic-recording ring-4 ring-error/20'
            : 'bg-surface-container-high text-primary hover:bg-primary hover:text-on-primary shadow-sm'
        } ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer active:scale-95'}`}
        title={isListening ? 'Stop Listening' : `Speak in ${language}`}
        aria-label={isListening ? 'Stop Voice Recording' : `Start Voice Input in ${language}`}
      >
        {isListening ? <MicOff className="w-5 h-5 animate-pulse" /> : <Mic className="w-5 h-5" />}
      </button>

      {isListening && (
        <div className="flex flex-col items-center">
          <span className="text-[11px] font-bold text-error animate-pulse">
            Listening ({language})...
          </span>
          {interimTranscript && (
            <p className="text-xs italic text-on-surface-variant max-w-[200px] truncate text-center mt-0.5">
              "{interimTranscript}"
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default VoiceInput;
