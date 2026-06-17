import { useCallback, useEffect, useRef, useState } from 'react'

export type MicrophoneStreamOptions = {
  mimeType?: string
  timesliceMs?: number
}

export function useMicrophoneStream(opts?: MicrophoneStreamOptions) {

  const timesliceMs = opts?.timesliceMs ?? 500
  const mimeType = opts?.mimeType

  const mediaStreamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)

  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const stop = useCallback(() => {
    try {
      recorderRef.current?.stop()
    } catch {
      // ignore
    }

    try {
      mediaStreamRef.current?.getTracks?.().forEach((t) => t.stop())
    } catch {
      // ignore
    }

    recorderRef.current = null
    mediaStreamRef.current = null
    setIsRecording(false)
  }, [])

  const start = useCallback(
    async (onChunk: (chunk: Blob) => void) => {
      setError(null)

      if (!navigator.mediaDevices?.getUserMedia) {
        setError('getUserMedia non supporté')
        return
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        mediaStreamRef.current = stream

        const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
        recorderRef.current = recorder

        recorder.ondataavailable = async (ev) => {
          if (!ev.data || ev.data.size === 0) return

          // Blob -> Base64 (required by WS contract)
          const buf = await ev.data.arrayBuffer()
          const bytes = new Uint8Array(buf)
          let binary = ''
          for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i])
          const base64 = btoa(binary)

          // We pass base64 string to caller for WS contract
          onChunk(base64 as any)
        }


        recorder.onerror = () => {
          setError('Erreur MediaRecorder')
          setIsRecording(false)
        }

        recorder.start(timesliceMs)
        setIsRecording(true)
      } catch (e: any) {
        setError(e?.message ?? 'Impossible d’accéder au microphone')
        setIsRecording(false)
      }
    },
    [mimeType, timesliceMs]
  )

  useEffect(() => {
    return () => stop()
  }, [stop])


  return {
    isRecording,
    error,
    start,
    stop,
  }
}

