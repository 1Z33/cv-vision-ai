/**
 * Hook React pour entretien vocal AI (version corrigée)
 * STT (Web Speech API) + TTS (Speech Synthesis)
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export interface VocalMessage {
  role: 'user' | 'ai';
  text: string;
  timestamp: number;
}

export interface VocalInterviewState {
  isListening: boolean;
  isSpeaking: boolean;
  isProcessing: boolean;
  messages: VocalMessage[];
  currentQuestion: string;
  currentQuestionNumber?: number;
  sessionStatus: 'idle' | 'active' | 'evaluating' | 'completed';
  error: string | null;
  totalScore?: number;

  source?: string;
  fallback_reason?: string;
}

export function useVocalInterview(sessionId: string) {
  const [state, setState] = useState<VocalInterviewState>({
    isListening: false,
    isSpeaking: false,
    isProcessing: false,
    messages: [],
    currentQuestion: '',
    currentQuestionNumber: undefined,
    sessionStatus: 'idle',
    error: null,
    source: undefined,
    fallback_reason: undefined,
  });

  const recognitionRef = useRef<any | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [transcript, setTranscript] = useState<string>('');

  const token = useMemo(() => localStorage.getItem('access_token'), []);

  useEffect(() => {
    const SpeechRecognitionImpl =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognitionImpl) {
      setState((prev) => ({
        ...prev,
        error: 'Votre navigateur ne supporte pas la reconnaissance vocale. Essayez Chrome.',
      }));
      return;
    }

    recognitionRef.current = new SpeechRecognitionImpl();
    recognitionRef.current.continuous = false;
    recognitionRef.current.interimResults = false;
    recognitionRef.current.lang = 'fr-FR';
    recognitionRef.current.maxAlternatives = 1;

    recognitionRef.current.onresult = (event: any) => {
      const text = event.results?.[0]?.[0]?.transcript ?? '';
      if (!text) return;
      setTranscript(text);
    };

    recognitionRef.current.onerror = (event: any) => {
      console.error('STT Error:', event.error);

      let errorMsg = 'Erreur de reconnaissance vocale';
      switch (event.error) {
        case 'no-speech':
          errorMsg = 'Aucune parole détectée. Essayez de parler plus fort.';
          break;
        case 'audio-capture':
          errorMsg = 'Microphone non accessible. Vérifiez vos permissions.';
          break;
        case 'not-allowed':
          errorMsg = 'Accès au microphone refusé. Autorisez-le dans les paramètres.';
          break;
        case 'network':
          errorMsg = 'Problème réseau. Vérifiez votre connexion.';
          break;
      }

      setState((prev) => ({
        ...prev,
        isListening: false,
        error: errorMsg,
      }));
    };

    recognitionRef.current.onend = () => {
      setState((prev) => ({ ...prev, isListening: false }));
    };

    return () => {
      try {
        recognitionRef.current?.stop?.();
      } catch {
        // ignore
      }
      abortControllerRef.current?.abort();
    };
  }, []);

  const speak = useCallback(async (text: string): Promise<void> => {
    return new Promise((resolve) => {
      if (!(window as any).speechSynthesis) {
        resolve();
        return;
      }

      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'fr-FR';
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      const voices = window.speechSynthesis.getVoices();
      const frenchVoice = voices.find((v) => v.lang?.startsWith('fr'));
      if (frenchVoice) utterance.voice = frenchVoice;

      utterance.onstart = () => setState((prev) => ({ ...prev, isSpeaking: true, error: null }));
      utterance.onend = () => {
        setState((prev) => ({ ...prev, isSpeaking: false }));
        resolve();
      };
      utterance.onerror = () => {
        setState((prev) => ({ ...prev, isSpeaking: false }));
        resolve();
      };

      window.speechSynthesis.speak(utterance);
    });
  }, []);

  const startInterview = useCallback(async () => {
    setTranscript('');
    setState((prev) => ({ ...prev, sessionStatus: 'active', isProcessing: true, error: null }));

    try {
      const response = await fetch(`/api/v1/interviews/${sessionId}/vocal-start`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();

      setState((prev) => ({
        ...prev,
        currentQuestion: data.question_text,
        currentQuestionNumber: data.question_number ?? 1,
        messages: [{ role: 'ai', text: data.question_text, timestamp: Date.now() }],
        isProcessing: false,
        source: data.source,
        fallback_reason: data.fallback_reason,
      }));

      await speak(data.question_text);
    } catch {
      setState((prev) => ({
        ...prev,
        isProcessing: false,
        error: 'Impossible de démarrer l’entretien. Réessayez.',
      }));
    }
  }, [sessionId, speak, token]);

  const listen = useCallback(() => {
    if (!recognitionRef.current) {
      setState((prev) => ({ ...prev, error: 'Reconnaissance vocale non disponible' }));
      return;
    }

    if (state.isSpeaking) {
      window.speechSynthesis.cancel();
      setState((prev) => ({ ...prev, isSpeaking: false }));
    }

    setState((prev) => ({ ...prev, isListening: true, error: null }));

    try {
      recognitionRef.current.start();
    } catch {
      setState((prev) => ({ ...prev, isListening: false }));
    }
  }, [state.isSpeaking]);

  const handleUserAnswer = useCallback(
    async (text: string, audioBlob: Blob) => {
      setState((prev) => ({
        ...prev,
        isListening: false,
        isProcessing: true,
        messages: [...prev.messages, { role: 'user', text, timestamp: Date.now() }],
      }));

      try {
        abortControllerRef.current = new AbortController();

        const mimeType = audioBlob.type || 'audio/webm';
        const extension = mimeType.includes('ogg')
          ? '.ogg'
          : mimeType.includes('webm')
            ? '.webm'
            : '.wav';

        const formData = new FormData();
        formData.append('audio', audioBlob, `answer${extension}`);

        if (state.currentQuestionNumber) {
          formData.append('question_number', String(state.currentQuestionNumber));
        }

        const response = await fetch(`/api/v1/interviews/${sessionId}/vocal-answer`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.is_complete) {
          setState((prev) => ({
            ...prev,
            sessionStatus: 'completed',
            isProcessing: false,
            totalScore: data.total_score,
            messages: [
              ...prev.messages,
              {
                role: 'ai',
                text: `Entretien terminé ! Score: ${data.total_score}/100. ${data.feedback_text || ''}`.trim(),
                timestamp: Date.now(),
              },
            ],
          }));

          if (data.feedback_text) await speak(data.feedback_text);
          return;
        }

        setState((prev) => ({
          ...prev,
          currentQuestion: data.next_question_text,
          currentQuestionNumber: data.next_question_number,
          isProcessing: false,
          messages: [...prev.messages, { role: 'ai', text: data.next_question_text, timestamp: Date.now() }],
        }));

        if (data.next_question_text) await speak(data.next_question_text);
      } catch (error: any) {
        if (error?.name === 'AbortError') return;
        setState((prev) => ({
          ...prev,
          isProcessing: false,
          error: 'Erreur de communication. Cliquez pour réessayer.',
        }));
      }
    },
    [sessionId, speak, state.currentQuestionNumber, token]
  );

  const submitAnswer = useCallback(
    async (audioBlob: Blob, text: string) => {
      return handleUserAnswer(text || '', audioBlob);
    },
    [handleUserAnswer]
  );

  const stopInterview = useCallback(() => {
    try {
      recognitionRef.current?.stop?.();
    } catch {
      // ignore
    }

    window.speechSynthesis?.cancel?.();
    abortControllerRef.current?.abort();

    setState((prev) => ({
      ...prev,
      isListening: false,
      isSpeaking: false,
      isProcessing: false,
      sessionStatus: 'idle',
    }));
  }, []);

  const retry = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
    if (state.sessionStatus === 'idle') startInterview();
    else listen();
  }, [listen, startInterview, state.sessionStatus]);

  return {
    ...state,
    transcript,
    startInterview,
    listen,
    stopInterview,
    retry,
    submitAnswer,
  };
}

declare global {
  interface Window {
    SpeechRecognition?: any;
    webkitSpeechRecognition?: any;
  }
}

