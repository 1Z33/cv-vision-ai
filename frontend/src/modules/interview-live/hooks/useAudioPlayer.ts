import { useCallback, useRef, useState } from 'react'

export function useAudioPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)

  const stop = useCallback(() => {
    try {
      audioRef.current?.pause()
      audioRef.current && (audioRef.current.currentTime = 0)
    } catch {
      // ignore
    }
    setIsPlaying(false)
  }, [])

  const playUrl = useCallback(async (url?: string) => {
    if (!url) return

    try {
      stop()
      const audio = new Audio(url)
      audioRef.current = audio

      audio.onended = () => setIsPlaying(false)
      audio.onerror = () => setIsPlaying(false)

      await audio.play()
      setIsPlaying(true)
    } catch {
      setIsPlaying(false)
    }
  }, [stop])

  const speakText = useCallback(async (text?: string) => {
    if (!text) return
    try {
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'fr-FR'
      utterance.rate = 0.92
      utterance.pitch = 1.0

      return await new Promise<void>((resolve) => {
        utterance.onstart = () => setIsPlaying(true)
        utterance.onend = () => {
          setIsPlaying(false)
          resolve()
        }
        utterance.onerror = () => {
          setIsPlaying(false)
          resolve()
        }
        window.speechSynthesis.speak(utterance)
      })
    } catch {
      // ignore
    }
  }, [])

  return {
    isPlaying,
    playUrl,
    speakText,
    stop,
  }
}

