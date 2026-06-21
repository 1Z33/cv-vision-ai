import { useState, useCallback, useRef } from 'react';

interface VocalInterviewState {
  isLoading: boolean;
  currentQuestion: string | null;
  currentQuestionNumber: number;
  transcript: string;
  feedback: string | null;
  score: number | null;
  isListening: boolean;
  error: string | null;
  geminiStatus: {
    source: 'gemini' | 'fallback' | null;
    fallbackReason: string | null;
    showNotice: boolean;
  };
}


export function useVocalInterview() {
  const [state, setState] = useState<VocalInterviewState>({
    isLoading: false,
    currentQuestion: null,
    currentQuestionNumber: 1,
    transcript: '',
    feedback: null,
    score: null,
    isListening: false,
    error: null,
    geminiStatus: {
      source: null,
      fallbackReason: null,
      showNotice: false,
    },
  });

  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Minimal types for browsers (avoid relying on lib.dom typings)
  type SpeechRecognition = {
    lang: string;
    continuous: boolean;
    interimResults: boolean;
    start: () => void;
    stop: () => void;
    onresult: ((event: SpeechRecognitionEvent) => void) | null;
    onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
    onend: (() => void) | null;
  };

  type SpeechRecognitionEvent = {
    resultIndex: number;
    results: Array<{
      isFinal: boolean;
      0: { transcript: string };
    }>;
  };

  type SpeechRecognitionErrorEvent = {
    error: string;
  };

  const playAudio = useCallback(async (url?: string, text?: string) => {
    try {
      if (url) {
        const audio = new Audio(url);
        try {
          audio.pause();
          audio.currentTime = 0;
        } catch {
          // ignore
        }
        await audio.play();
        return;
      }

      if (text && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'fr-FR';
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
      }
    } catch {
      if (text && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = 'fr-FR';
          utterance.rate = 0.9;
          utterance.pitch = 1.0;
          window.speechSynthesis.speak(utterance);
        } catch {
          // ignore
        }
      }
    }
  }, []);

  const startInterview = useCallback(async (sessionId: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
const apiBase = import.meta.env.VITE_API_URL || '/api';
      const res = await fetch(`${apiBase}/v1/interviews/${sessionId}/vocal-start`, {


        method: 'POST',

        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
        },
      });
      const data = await res.json();

      setState(prev => ({
        ...prev,
        isLoading: false,
        currentQuestion: data.question?.question_text || data.question_text || null,
        currentQuestionNumber: data.question?.question_number || data.question_number || 1,
        geminiStatus: {
          source: data.source || 'gemini',
          fallbackReason: data.fallback_reason || null,
          showNotice: data.source === 'fallback',
        },
      }));

      // Prefer backend audio URL when available (fallback might not provide it)
      const questionText = data.question?.question_text || data.question_text || '';
      const questionAudioUrl = data.question_audio_url || data.question?.question_audio_url;
      await playAudio(questionAudioUrl, questionText);

      return data;
    } catch (e) {
      setState(prev => ({ ...prev, isLoading: false, error: (e as Error).message }));
      throw e;
    }
  }, [playAudio]);

  const startListening = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setState(prev => ({ ...prev, error: 'SpeechRecognition non supporte' }));
      return;
    }

    const SpeechRecognitionImpl =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    const recognition: SpeechRecognition = new SpeechRecognitionImpl();
    recognition.lang = 'fr-FR';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }

      if (finalTranscript) {
        setState(prev => ({ ...prev, transcript: (prev.transcript + ' ' + finalTranscript).trim() }));
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      setState(prev => ({ ...prev, isListening: false, error: event.error }));
    };

    recognition.onend = () => {
      setState(prev => ({ ...prev, isListening: false }));
    };

    // Clear transcript only AFTER creating recognition to avoid races
    // between STT final results and UI enabling.
    recognition.start();
    recognitionRef.current = recognition;
    setState(prev => ({ ...prev, isListening: true, transcript: '' }));
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setState(prev => ({ ...prev, isListening: false }));
  }, []);

  const submitAnswer = useCallback(
    async (sessionId: string, questionNumber: number) => {
      const text = state.transcript.trim();
      console.log('[HOOK] submitAnswer called:', {
        sessionId,
        questionNumber,
        textLength: text.length,
      });

      if (!text) {
        console.error('[HOOK] submitAnswer blocked: empty transcript');
        setState(prev => ({ ...prev, error: 'Aucune transcription disponible' }));
        return;
      }

      setState(prev => ({ ...prev, isLoading: true, error: null }));

      try {
        const formData = new FormData();
        formData.append('answer_text', text);
        formData.append('question_number', String(questionNumber));

        console.log('[HOOK] Sending to /vocal-answer:', {
          sessionId,
          questionNumber,
          text: text.substring(0, 50),
        });

        const apiBase = import.meta.env.VITE_API_URL || '/api';
        const response = await fetch(
          `${apiBase}/v1/interviews/${sessionId}/vocal-answer`,
          {

            method: 'POST',
            headers: {
              Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
            },
            body: formData,
          },
        );

        console.log('[HOOK] Response status:', response.status);

        // Lire le body même en erreur
        const responseText = await response.text();
        console.log('[HOOK] Response body:', responseText);

        if (!response.ok) {
          let errorDetail = `HTTP ${response.status}`;
          try {
            const errorJson = JSON.parse(responseText);
            errorDetail =
              errorJson.detail || errorJson.message || responseText;
          } catch {
            errorDetail = responseText || `HTTP ${response.status}`;
          }
          throw new Error(errorDetail);
        }

        const data = JSON.parse(responseText);
        console.log('[HOOK] Success:', data);

        setState(prev => ({
          ...prev,
          isLoading: false,
          feedback: data.feedback || null,
          score: data.score || null,
          transcript: '',
          currentQuestion:
            data.next_question_text ||
            data.next_question?.question_text ||
            null,
          currentQuestionNumber:
            data.next_question_number ||
            data.next_question?.question_number ||
            questionNumber + 1,
        }));

        // Play feedback + next question when present
        const feedbackText = data.feedback_text || data.feedback || '';
        const nextQuestionText =
          data.next_question_text || data.next_question?.question_text || '';
        const feedbackAudioUrl = data.feedback_audio_url;
        const nextQuestionAudioUrl = data.next_question_audio_url;

        if (data.is_complete) {
          if (feedbackText) await playAudio(undefined, feedbackText);
          setState(prev => ({
            ...prev,
            isLoading: false,
            currentQuestion: null,
          }));
          return data;
        }

        if (feedbackText) await playAudio(feedbackAudioUrl, feedbackText);
        if (nextQuestionText)
          await playAudio(nextQuestionAudioUrl, nextQuestionText);

        return data;
      } catch (e) {
        console.error('[HOOK] submitAnswer error:', e);
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: (e as Error).message,
        }));
        throw e;
      }
    },
    [playAudio, state.transcript],
  );

  const dismissNotice = useCallback(() => {
    setState(prev => ({
      ...prev,
      geminiStatus: { ...prev.geminiStatus, showNotice: false },
    }));
  }, []);

  return {
    ...state,
    startInterview,
    startListening,
    stopListening,
    submitAnswer,
    dismissNotice,
  };
}

