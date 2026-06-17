import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Mic, MicOff, Loader2, Volume2, Square } from 'lucide-react'
import { useWebSocketInterview } from '../hooks/useWebSocketInterview'
import { useMicrophoneStream } from '../hooks/useMicrophoneStream'
import { useAudioPlayer } from '../hooks/useAudioPlayer'
import { ChatTurn } from '../types'

type Props = {
  sessionId: string
}

function VoiceWaveVisualizer() {
  return (
    <div className="flex items-center gap-2" aria-hidden>
      {[...Array(12)].map((_, i) => (
        <div
          key={i}
          className="w-1 bg-primary-500/70 rounded"
          style={{ height: 6 + Math.round(Math.random() * 18) }}
        />
      ))}
    </div>
  )
}

export default function LiveInterviewScreen({ sessionId }: Props) {
  const { state, sendUserAnswerText, close, restartInterview } = useWebSocketInterview(sessionId)

  if (state.status === 'completed') {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white/5 border border-white/10 rounded-xl p-6">
          <div className="text-sm text-gray-400">Résultat final</div>
          <div className="text-4xl font-bold text-primary-300 mt-2">{state.finalScore ?? '—'}/100</div>
          <div className="text-sm text-gray-300 mt-3 whitespace-pre-wrap">{state.finalSummary ?? '—'}</div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={restartInterview}
              className="px-4 py-3 rounded-full text-sm font-medium transition-all bg-green-500/20 border border-green-500/30 text-green-100 hover:bg-green-500/25"
            >
              Réessayer
            </button>
            <button
              type="button"
              onClick={close}
              className="px-4 py-3 rounded-full text-sm font-medium transition-all bg-white/5 border border-white/10 text-white hover:bg-white/10"
            >
              Quitter
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (state.connectionError || state.quotaError || state.error) {

    const msg = state.connectionError || state.quotaError || state.error

    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <div className="text-sm text-gray-300">{msg}</div>
          <button
            type="button"
            onClick={restartInterview}
            className="mt-4 px-4 py-3 rounded-full text-sm font-medium transition-all bg-green-500/20 border border-green-500/30 text-green-100 hover:bg-green-500/25"
          >
            Réessayer
          </button>
          {state.isReconnecting ? (
            <div className="mt-3 text-sm text-gray-300">Reconnexion…</div>
          ) : null}
        </div>
      </div>
    )
  }

  const { isPlaying, playUrl, speakText, stop } = useAudioPlayer()
  const mic = useMicrophoneStream({ timesliceMs: 700 })

  const [draftText, setDraftText] = useState('')

  const canSpeak = useMemo(() => !!state.currentQuestion?.text, [state.currentQuestion?.text])

  useEffect(() => {
    const audioUrl = state.currentQuestion?.audioUrl
    if (audioUrl) playUrl(audioUrl)
    else if (state.currentQuestion?.text) speakText(state.currentQuestion.text)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.currentQuestion?.audioUrl, state.currentQuestion?.text])

  useEffect(() => {
    return () => {
      stop()
      close()
    }
  }, [close, stop])

  const onMicStart = useCallback(async () => {
    // MVP: we only capture microphone chunks but send text transcript via UI text entry (no STT yet)
    // Backend may accept audio chunks in phase 2.
    await mic.start(() => {
      // no-op for MVP
    })
  }, [mic])

  const onMicStop = useCallback(() => {
    mic.stop()
  }, [mic])

  const handleSend = useCallback(() => {
    const text = draftText.trim()
    if (!text) return
    sendUserAnswerText(text)
    setDraftText('')
  }, [draftText, sendUserAnswerText])

  const speaking = isPlaying || state.status === 'speaking'

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-sm text-gray-400">Live Interview</div>
          <div className="text-2xl font-bold">🎙️ ChatGPT Voice-like</div>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-400">Statut</div>
          <div className="font-medium">{state.status}</div>
        </div>
      </div>

      {/* Recruiter avatar / speaking indicator */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center gap-4">
        <div className="w-14 h-14 rounded-full bg-primary-500/20 border border-primary-500/30 flex items-center justify-center">
          <Volume2 className={speaking ? 'animate-pulse' : ''} />
        </div>
        <div className="flex-1">
          <div className="font-semibold">Recruteur IA</div>
          <div className="text-sm text-gray-400">
            {speaking ? 'L’IA parle…' : state.currentQuestion?.text ? 'Question en attente…' : 'Connexion…'}
          </div>
          <div className="mt-2">
            {speaking ? <VoiceWaveVisualizer /> : null}
          </div>
        </div>
      </div>

      {/* Question */}
      {state.currentQuestion?.text ? (
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <div className="text-xs text-gray-400">Question {state.currentQuestion?.number ?? ''}</div>
          <div className="text-lg font-semibold mt-1">{state.currentQuestion.text}</div>
        </div>
      ) : null}

      {/* Transcript / history */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <div className="font-semibold">Conversation</div>
          <div className="mt-3 space-y-3 max-h-72 overflow-auto pr-1">
            {state.messages.map((m: ChatTurn) => (
              <div key={m.id} className={m.role === 'user' ? 'text-right' : 'text-left'}>
                <div
                  className={
                    m.role === 'user'
                      ? 'inline-block bg-primary-500/15 border border-primary-500/20 rounded-lg px-3 py-2 text-sm'
                      : m.role === 'ai'
                        ? 'inline-block bg-blue-500/10 border border-blue-500/20 rounded-lg px-3 py-2 text-sm'
                        : 'inline-block bg-gray-500/10 border border-gray-500/20 rounded-lg px-3 py-2 text-sm'
                  }
                >
                  {m.text}
                </div>
              </div>
            ))}
            {state.messages.length === 0 ? (
              <div className="text-sm text-gray-400">En attente…</div>
            ) : null}
          </div>
        </div>

        {/* Score / feedback */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <div className="font-semibold">Feedback live</div>
          <div className="mt-3">
            {state.analysis ? (
              <>
                <div className="text-3xl font-bold text-primary-300">
                  {state.analysis.score ?? '—'}/100
                </div>
                <div className="text-sm text-gray-300 mt-2">
                  {state.analysis.feedbackText || '—'}
                </div>
                {state.analysis.scores ? (
                  <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                    {Object.entries(state.analysis.scores).map(([k, v]) => (
                      <div key={k} className="bg-white/5 rounded-lg border border-white/10 p-2">
                        <div className="text-gray-400 capitalize">{k}</div>
                        <div className="font-semibold text-white">{v}</div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </>
            ) : (
              <div className="text-sm text-gray-400">Dès que l’IA analyse votre réponse…</div>
            )}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="font-semibold">Votre réponse</div>
            <div className="text-sm text-gray-400">
              MVP: envoyez via texte (micro chunk prêt pour phase 2)
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={mic.isRecording ? onMicStop : onMicStart}
              className={`px-4 py-3 rounded-full text-sm font-medium transition-all border ${
                mic.isRecording
                  ? 'bg-red-500/20 border-red-500/40 text-red-200'
                  : 'bg-primary-500/15 border-primary-500/30 text-primary-200'
              }`}
              disabled={state.status === 'connecting'}
            >
              {mic.isRecording ? (
                <span className="inline-flex items-center gap-2">
                  <MicOff className="w-4 h-4" /> Stop micro
                </span>
              ) : (
                <span className="inline-flex items-center gap-2">
                  <Mic className="w-4 h-4" /> Parler
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={handleSend}
              disabled={!draftText.trim() || state.status === 'connecting'}
              className="px-4 py-3 rounded-full text-sm font-medium transition-all bg-green-500/20 border border-green-500/30 text-green-100 hover:bg-green-500/25"
            >
              Envoyer
            </button>
          </div>
        </div>

        {mic.error ? (
          <div className="mt-3 text-sm text-red-300">{mic.error}</div>
        ) : null}

        <textarea
          value={draftText}
          onChange={(e) => setDraftText(e.target.value)}
          placeholder="Écrivez votre réponse…"
          rows={4}
          className="mt-4 w-full px-4 py-3 bg-dark-800/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
        />

        {state.error ? (
          <div className="mt-3 text-sm text-red-300">{state.error}</div>
        ) : null}

        {state.status === 'connecting' ? (
          <div className="mt-3 flex items-center gap-2 text-sm text-gray-300">
            <Loader2 className="w-4 h-4 animate-spin" /> Connexion WebSocket…
          </div>
        ) : null}
      </div>
    </div>
  )
}

