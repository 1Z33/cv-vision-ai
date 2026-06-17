import { useCallback, useEffect, useRef, useState } from 'react';

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const stopTracks = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    streamRef.current = null;
  }, []);

  useEffect(() => {
    return () => {
      try {
        mediaRecorderRef.current?.state === 'recording' && mediaRecorderRef.current.stop();
      } catch {
        // ignore
      }
      stopTracks();
    };
  }, [stopTracks]);

  const startRecording = useCallback(async () => {
    setAudioBlob(null);

    // Prefer WebM where supported
    const mimeTypeCandidates = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/ogg',
    ];

    const mimeType = mimeTypeCandidates.find((t) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const MR: any = window.MediaRecorder;
      return typeof MR?.isTypeSupported === 'function' ? MR.isTypeSupported(t) : true;
    });

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const options = mimeType ? { mimeType } : undefined;
      const recorder = new MediaRecorder(stream, options as MediaRecorderOptions | undefined);

      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        const finalMimeType = recorder.mimeType || mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: finalMimeType });
        setAudioBlob(blob);
        stopTracks();
      };

      recorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Erreur accès micro:', error);
      stopTracks();
      setIsRecording(false);
    }
  }, [stopTracks]);

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    const recorder = mediaRecorderRef.current;
    if (!recorder) return null;

    if (recorder.state !== 'recording') {
      return audioBlob;
    }

    // Stop timer is implicit in this simpler hook; we just resolve after onstop.
    try {
      return await new Promise((resolve) => {
        const check = setInterval(() => {
          if (recorder.state === 'inactive') {
            clearInterval(check);
            resolve(audioBlob);
          }
        }, 100);

        // Ensure final chunk is collected
        try {
          recorder.requestData();
        } catch {
          // ignore
        }

        try {
          recorder.stop();
        } catch {
          clearInterval(check);
          resolve(null);
        }

        setTimeout(() => {
          clearInterval(check);
          resolve(audioBlob);
        }, 3000);
      });
    } finally {
      setIsRecording(false);
    }
  }, [audioBlob]);



  const reset = useCallback(() => setAudioBlob(null), []);

  return {
    isRecording,
    audioBlob,
    startRecording,
    stopRecording,
    reset,
  };
}


