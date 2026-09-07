import { useState, useEffect, useRef, useCallback } from 'react';

interface SpeechRecognitionOptions {
  language?: string;
  onFinalTranscript?: (text: string) => void;
  onError?: (error: string) => void;
}

export function useSpeechRecognition({
  language = 'English',
  onFinalTranscript,
  onError,
}: SpeechRecognitionOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(true);
  const recognitionRef = useRef<any>(null);

  // Map application language to BCP 47 language tag
  const getLanguageTag = useCallback((lang: string): string => {
    switch (lang.toLowerCase()) {
      case 'hindi':
        return 'hi-IN';
      case 'marathi':
        return 'mr-IN';
      case 'english':
      default:
        return 'en-IN';
    }
  }, []);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = getLanguageTag(language);

    recognition.onstart = () => {
      setIsListening(true);
      setInterimTranscript('');
    };

    recognition.onresult = (event: any) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const item = event.results[i];
        if (item.isFinal) {
          final += item[0].transcript;
        } else {
          interim += item[0].transcript;
        }
      }

      setInterimTranscript(interim);
      if (final) {
        const fullFinal = final.trim();
        setTranscript((prev) => (prev ? `${prev} ${fullFinal}` : fullFinal));
        if (onFinalTranscript) {
          onFinalTranscript(fullFinal);
        }
      }
    };

    recognition.onerror = (event: any) => {
      console.warn('Speech recognition error:', event.error);
      setIsListening(false);
      if (onError) {
        onError(event.error);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      setInterimTranscript('');
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.abort();
      } catch {
        // Ignore abort errors on unmount
      }
    };
  }, [language, getLanguageTag, onFinalTranscript, onError]);

  const startListening = useCallback(() => {
    if (!recognitionRef.current || isListening) return;
    try {
      recognitionRef.current.lang = getLanguageTag(language);
      recognitionRef.current.start();
      setIsListening(true);
    } catch (err) {
      console.warn('Failed to start speech recognition:', err);
    }
  }, [isListening, language, getLanguageTag]);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !isListening) return;
    try {
      recognitionRef.current.stop();
      setIsListening(false);
    } catch (err) {
      console.warn('Failed to stop speech recognition:', err);
    }
  }, [isListening]);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
  }, []);

  return {
    isSupported,
    isListening,
    transcript,
    interimTranscript,
    startListening,
    stopListening,
    resetTranscript,
  };
}
