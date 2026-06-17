import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { InterviewSocket } from '../services/interviewSocket'
import {
  ChatTurn,
  InterviewLiveEventMessage,
  LiveAnalysisPayload,
  LiveQuestionPayload,
  LiveSessionStatus,
} from '../types'

type UseWebSocketInterviewState = {
  status: LiveSessionStatus
  currentQuestion: {
    text: string
    number?: number
    audioUrl?: string
  } | null
  analysis: {
    score: number | null
    feedbackText: string | null
    scores?: Record<string, number>
  } | null
  error: string | null
  connectionError: string | null
  quotaError: string | null
  isReconnecting: boolean
  messages: ChatTurn[]
}

function safeString(v: any): string {
  if (typeof v === 'string') return v
  if (v == null) return ''
  return String(v)
}

export function useWebSocketInterview(sessionId: string | null | undefined) {
  const token = useMemo(() => localStorage.getItem('access_token') || undefined, [])

  const [state, setState] = useState<UseWebSocketInterviewState & { finalScore?: number | null; finalSummary?: string | null }>({
    status: 'idle',

    currentQuestion: null,
    analysis: null,
    error: null,
    connectionError: null,
    quotaError: null,
    isReconnecting: false,
    messages: [],
  })

  const socketRef = useRef<InterviewSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)

  const connect = useCallback(() => {
    if (!sessionId) return

    setState((prev) => ({
      ...prev,
      status: 'connecting',
      error: null,
      connectionError: null,
      quotaError: null,
      isReconnecting: false,
    }))

    const socket = new InterviewSocket({
      sessionId,
      accessToken: token,
    })

    socketRef.current = socket

    socket.onOpen = () => {
      reconnectAttemptsRef.current = 0
      setState((prev) => ({
        ...prev,
        status: 'active',
        isReconnecting: false,
      }))
    }

    socket.onMessage = (msg: InterviewLiveEventMessage) => {
      const event = msg.event
      const payload = msg.payload ?? {}

      if (event === 'session_started') {
        setState((prev) => ({
          ...prev,
          status: 'active',
          messages: [...prev.messages],
        }))
        return
      }

      if (event === 'question') {
        const q = payload as LiveQuestionPayload
        const text = (q as any).question_text ?? (q as any).question?.question_text ?? safeString((q as any).question_text)
        const number = (q as any).question_number ?? (q as any).question?.question_number
        const audioUrl = q.audio_url ?? (q as any).audio?.url

        setState((prev) => ({
          ...prev,
          currentQuestion: { text, number, audioUrl },
          analysis: null,
          messages: [
            ...prev.messages,
            { id: crypto.randomUUID?.() ?? String(Date.now()), role: 'ai', text, timestamp: Date.now() },
          ],
          status: 'active',
        }))
        return
      }

      if (event === 'analysis') {
        const a = payload as LiveAnalysisPayload
        const score = typeof a.score === 'number' ? a.score : null
        const feedbackText = a.feedback_text ?? a.feedback ?? null

        setState((prev) => ({
          ...prev,
          analysis: {
            score,
            feedbackText,
            scores: a.scores,
          },
          status: 'evaluating',
          messages: [
            ...prev.messages,
            ...(feedbackText
              ? [
                  {
                    id: crypto.randomUUID?.() ?? String(Date.now()),
                    role: 'system',
                    text: feedbackText,
                    timestamp: Date.now(),
                  } as ChatTurn,
                ]
              : []),
          ],
        }))
        return
      }

      if (event === 'analysis_update') {
        // UX: optionnel; pas de logique métier
        return
      }

      if (event === 'quota_exceeded') {
        const msg = (payload as any)?.message
        setState((prev) => ({
          ...prev,
          quotaError: String(msg ?? 'Quota Gemini atteint. Veuillez réessayer plus tard.'),
          connectionError: null,
          status: 'error',
        }))
        return
      }

      if (event === 'error') {
        const msg = (payload as any)?.message ?? 'L\'IA est momentanément indisponible. Veuillez réessayer.'
        setState((prev) => ({
          ...prev,
          error: String(msg),
          connectionError: prev.connectionError,
          quotaError: prev.quotaError,
          status: 'error',
        }))
        return
      }


      if (event === 'session_finished') {
        const p = payload as any
        const finalScore = typeof p?.final_score === 'number' ? p.final_score : null
        const finalSummary = p?.summary ?? null

        setState((prev) => ({
          ...prev,
          status: 'completed',
          finalScore,
          finalSummary,
        }))
        // Socket will be closed by UI cleanup, but we can proactively close too.
        try {
          socketRef.current?.close()
        } catch {
          // ignore
        }
        return
      }

      if (event === 'connection_lost') {

        setState((prev) => ({
          ...prev,
          connectionError: 'Connexion perdue',
          status: 'error',
        }))
        return
      }

      // Strict contract: ignore any other events
    }

    socket.onClose = (ev) => {
      const canReconnect = reconnectAttemptsRef.current < 10
      const shouldReconnect = !ev.wasClean && canReconnect

      if (shouldReconnect) {
        const delay = Math.min(2000 * Math.pow(2, reconnectAttemptsRef.current), 15000)
        reconnectAttemptsRef.current += 1
        setState((prev) => ({
          ...prev,
          status: 'connecting',
          isReconnecting: true,
          connectionError: prev.connectionError ?? 'Connexion perdue',
        }))
        setTimeout(() => {
          try {
            socket.reconnect()
          } catch {
            // ignore
          }
        }, delay)
      } else {
        setState((prev) => ({
          ...prev,
          status: 'error',
          connectionError: prev.connectionError ?? `Connexion perdue (${ev.code})`,
          isReconnecting: false,
        }))
      }
    }

    socket.onError = () => {
      setState((prev) => ({
        ...prev,
        status: prev.status === 'connecting' ? 'connecting' : 'error',
        connectionError: prev.connectionError ?? 'Erreur réseau',
      }))
    }

    socket.connect()

    return () => {
      try {
        socket.close()
      } catch {
        // ignore
      }
    }
  }, [sessionId, token])

  useEffect(() => {
    if (!sessionId) return
    return connect()
  }, [sessionId, connect])

  const restartInterview = useCallback(() => {
    socketRef.current?.close()
    socketRef.current = null
    setState((prev) => ({
      ...prev,
      status: 'connecting',
      error: null,
      connectionError: null,
      quotaError: null,
      isReconnecting: true,
    }))
    connect()
  }, [connect])

  const sendUserAnswerText = useCallback((text: string) => {
    if (!socketRef.current) return
    socketRef.current.sendEvent('user_answer', { text })

    setState((prev) => ({
      ...prev,
      messages: [
        ...prev.messages,
        {
          id: crypto.randomUUID?.() ?? String(Date.now()),
          role: 'user',
          text,
          timestamp: Date.now(),
        },
      ],
      status: 'listening',
    }))
  }, [])

  const sendUserAnswerAudioChunk = useCallback((chunk: any) => {
    if (!socketRef.current) return
    // WS contract: { event: 'audio_chunk', payload: { chunk: BASE64_AUDIO } }
    socketRef.current.sendEvent('audio_chunk', { chunk })
  }, [])

  const close = useCallback(() => {
    socketRef.current?.close()
    socketRef.current = null
    setState((prev) => ({ ...prev, status: 'idle' }))
  }, [])

  return {
    state,
    sendUserAnswerText,
    sendUserAnswerAudioChunk,
    close,
    restartInterview,
  }
}

