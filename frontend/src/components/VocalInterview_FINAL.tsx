/**
 * Composant Entretien Vocal AI (version corrigée)
 */

import React, { useState } from 'react';

import { useVocalInterview } from '../hooks/useVocalInterview_FINAL';
import { useAudioRecorder } from '../hooks/useAudioRecorder';

import { Mic, RotateCcw, AlertCircle, Loader } from 'lucide-react';

interface VocalInterviewProps {
  sessionId: string;
}

export const VocalInterview: React.FC<VocalInterviewProps> = ({ sessionId }) => {
  const {
    isListening,
    isSpeaking,
    isProcessing,
    messages,
    sessionStatus,
    error,
    startInterview,
    listen,
    stopInterview,
    retry,
    submitAnswer,
    transcript,
  } = useVocalInterview(sessionId);

  const { isRecording, audioBlob, startRecording, stopRecording } = useAudioRecorder();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showMyAnswer, setShowMyAnswer] = useState(false);
  const [myAnswerLoading, setMyAnswerLoading] = useState(false);
  const [replayLoading, setReplayLoading] = useState(false);

  const [myAnswer, setMyAnswer] = useState<{
    question_text: string;
    user_answer_text: string;
    feedback_text: string | null;
    answer_score: number | null;
    question_number: number;
  } | null>(null);

  if (sessionStatus === 'idle') {
    return (
      <div className="vocal-interview-start flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl min-h-[400px]">
        <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mb-6 shadow-lg">
          <Mic size={40} className="text-white" />
        </div>

        <h2 className="text-2xl font-bold text-gray-800 mb-2">Entretien Vocal AI</h2>
        <p className="text-gray-600 text-center mb-8 max-w-md">
          Passez votre entretien en parlant avec notre IA. Elle vous posera des questions et évaluera vos réponses.
        </p>

        {error && (
          <div className="flex items-center gap-2 text-red-600 bg-red-50 px-4 py-2 rounded-lg mb-4">
            <AlertCircle size={18} />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <button
          onClick={error ? retry : startInterview}
          className="flex items-center gap-3 px-8 py-4 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl"
        >
          {error ? 'Réessayer' : "Démarrer l'entretien"}
        </button>

        <p className="text-xs text-gray-400 mt-4">Nécessite Chrome/Edge avec microphone</p>
      </div>
    );
  }

  return (
    <div className="vocal-interview-active flex flex-col h-full bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${
              isListening
                ? 'bg-red-500 animate-pulse'
                : isSpeaking
                  ? 'bg-blue-500 animate-pulse'
                  : 'bg-green-500'
            }`}
          />
          <span className="text-sm font-medium text-gray-700">
            {isListening
              ? 'Écoute en cours...'
              : isSpeaking
                ? 'Lecture...'
                : isProcessing
                  ? 'Traitement...'
                  : 'En attente'}
          </span>
        </div>

        <button
          onClick={async () => {
            // Crucial: arrêter l'enregistrement + envoyer au backend
            if (isSubmitting) return;
            setIsSubmitting(true);
            try {
              const blob = await stopRecording();
              if (blob) {
                await submitAnswer(blob, transcript);
              }
              stopInterview();
            } finally {
              setIsSubmitting(false);
            }
          }}
          disabled={isProcessing || isSubmitting || isSpeaking}
          className="flex items-center gap-2 px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-lg transition"
        >
          <span className="text-sm">Arrêter</span>
