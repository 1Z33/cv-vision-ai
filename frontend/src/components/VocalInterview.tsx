import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useVocalInterview } from '../hooks/useVocalInterview_FINAL';
import GeminiNotice from './GeminiNotice';
import { Mic, MicOff, Loader2, Send } from 'lucide-react';

interface VocalInterviewProps {
  sessionId?: string;
  onTranscriptChange?: (text: string) => void;
  isEmbedded?: boolean;
}

export function VocalInterview({ sessionId: propSessionId, onTranscriptChange, isEmbedded = false }: VocalInterviewProps) {
  const { sessionId: paramSessionId } = useParams<{ sessionId: string }>();
  const sessionId = propSessionId || paramSessionId;

  const {
    startInterview,
    startListening,
    stopListening,
    submitAnswer,
    dismissNotice,
    currentQuestion,
    currentQuestionNumber,
    transcript,
    feedback,
    score,
    isLoading,
    isListening,
    geminiStatus,
    error,
  } = useVocalInterview();

  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (sessionId && !started) {
      startInterview(sessionId);
      setStarted(true);
    }
  }, [sessionId, started, startInterview]);

  useEffect(() => {
    if (onTranscriptChange && transcript) {
      onTranscriptChange(transcript);
    }
  }, [transcript, onTranscriptChange]);

  const handleToggleListen = () => {
    if (isListening) stopListening();
    else startListening();
  };

  const handleSubmit = async () => {
    if (!sessionId) return;

    // 1. Arrêter l'écoute
    if (isListening) {
      stopListening();
    }

    // 2. Attendre que le state se mette à jour (transcript final)
    await new Promise(resolve => setTimeout(resolve, 800));

    // 3. Lire le transcript (maintenant à jour)
    const text = transcript.trim();
    console.log("[UI] Submit - transcript after stop:", text);

    if (!text) {
      console.error("[UI] Submit blocked: transcript still empty after stop");
      return;
    }

    try {
      await submitAnswer(sessionId, currentQuestionNumber);
    } catch (e) {
      console.error("[UI] Submit error:", e);
    }
  };

  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded p-4 text-red-800">Erreur: {error}</div>
      </div>
    );
  }

  return (
    <div className={isEmbedded ? "space-y-4" : "max-w-3xl mx-auto p-6 space-y-6"}>
      {geminiStatus?.showNotice && !isEmbedded && (
        <GeminiNotice
          message="Mode local active - SpeechRecognition navigateur utilise"
          fallbackReason={geminiStatus.fallbackReason}
        />
      )}

      {/* Affiche l'erreur backend en clair */}
      {error && !isEmbedded && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          <strong>Erreur:</strong> {error}
        </div>
      )}

      {!isEmbedded && (
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">
            Entretien Vocal
            {geminiStatus?.source === 'fallback' && (
              <span className="ml-2 text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">Mode local</span>
            )}
          </h1>
          <span className="text-gray-500">Question {currentQuestionNumber}</span>
        </div>
      )}

      {currentQuestion && !isEmbedded && (
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <p className="text-lg">{currentQuestion}</p>
        </div>
      )}

      <div className="flex justify-center gap-4">
        <button
          onClick={handleToggleListen}
          disabled={isLoading}
          className={`flex items-center gap-2 px-8 py-4 rounded-full text-lg font-medium transition-all
            ${isListening
              ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
              : 'bg-blue-500 hover:bg-blue-600 text-white'}`}
        >
          {isListening ? (
            <>
              <MicOff className="h-6 w-6" /> Arreter l ecoute
            </>
          ) : (
            <>
              <Mic className="h-6 w-6" /> Repondre
            </>
          )}
        </button>

        {transcript.trim() && !isListening && !isEmbedded && (
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="flex items-center gap-2 px-6 py-4 rounded-full text-lg font-medium bg-green-500 hover:bg-green-600 text-white disabled:opacity-50"
          >
            <Send className="h-6 w-6" />
            Envoyer
          </button>
        )}

        {/* Si transcript vide mais on vient juste de soumettre */}
        {!transcript.trim() && !isListening && !isLoading && !isEmbedded && (
          <button
            disabled={true}
            className="flex items-center gap-2 px-6 py-4 rounded-full text-lg font-medium bg-green-500/40 text-white opacity-60 cursor-not-allowed"
            title="Parlez puis attendez que la transcription apparaisse"
          >
            <Send className="h-6 w-6" />
            Envoyer
          </button>
        )}
      </div>

      {isListening && (
        <div className="text-center text-red-500 animate-pulse">Ecoute en cours... Parlez maintenant</div>
      )}

      {transcript && !isEmbedded && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Votre reponse:</h3>
          <p className="text-gray-800">{transcript}</p>
        </div>
      )}

      {feedback && !isEmbedded && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-900">{feedback}</p>
          {score !== null && <p className="mt-2 text-blue-700 font-bold">Score: {score}/100</p>}
        </div>
      )}

      {isLoading && (
        <div className="flex justify-center gap-2 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          Traitement...
        </div>
      )}
    </div>
  );
}