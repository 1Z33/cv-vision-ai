import React, { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import LiveInterviewScreen from '../modules/interview-live/components/LiveInterviewScreen'

export default function LiveInterviewPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [mode, setMode] = useState<'live' | 'classic'>('live')

  // MVP feature-flag: INTERVIEW_MODE=classic|live
  // Uses Vite env if available; fallback to localStorage.
  const envMode = useMemo(() => {
    // eslint-disable-next-line no-undef
    const v = (import.meta as any)?.env?.VITE_INTERVIEW_MODE
    if (typeof v === 'string' && v) return v
    const stored = localStorage.getItem('INTERVIEW_MODE')
    return stored || ''
  }, [])

  useEffect(() => {
    if (envMode === 'classic' || envMode === 'live') setMode(envMode)
  }, [envMode])

  if (!sessionId) {
    return (
      <div className="max-w-3xl mx-auto p-6 text-red-300">
        sessionId manquant.
      </div>
    )
  }

  if (mode !== 'live') {
    // Classic fallback is handled by existing /interview route.
    // Redirecting would need react-router navigation; keep MVP simple.
    return (
      <div className="max-w-3xl mx-auto p-6 text-gray-200">
        Mode classic activé — utilisez la page /interview.
      </div>
    )
  }

  return <LiveInterviewScreen sessionId={sessionId} />
}

