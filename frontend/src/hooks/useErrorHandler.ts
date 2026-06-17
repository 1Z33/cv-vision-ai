import { useState, useCallback, useRef } from 'react';
import type { ErrorState } from '../components/ErrorHandler';

interface UseErrorHandlerOptions {
  maxRetries?: number;
  onQuotaExceeded?: () => void;
}

export function useErrorHandler(options: UseErrorHandlerOptions = {}) {
  const { maxRetries = 3, onQuotaExceeded } = options;

  const [error, setError] = useState<ErrorState | null>(null);
  const retryCountRef = useRef<number>(0);
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);


  const parseError = useCallback(
    (err: any): ErrorState => {
      const status = err?.status ?? err?.response?.status;
      const msg = String(err?.message || err?.detail || err || '');

      // Quota / rate limit
      if (
        status === 429 ||
        msg.includes('429') ||
        msg.toLowerCase().includes('quota') ||
        msg.includes('RESOURCE_EXHAUSTED')
      ) {
        return {
          type: 'quota',
          message: 'Quota API épuisé. Veuillez patienter avant de réessayer.',
          retryCount: retryCountRef.current,
          maxRetries,
          canRetry: retryCountRef.current < maxRetries,
          retryAfter: err?.retryAfter || 60,
        };
      }

      // Network
      if (
        !navigator.onLine ||
        msg.toLowerCase().includes('network') ||
        msg.toLowerCase().includes('failed to fetch') ||
        msg.includes('ECONNREFUSED') ||
        msg.toLowerCase().includes('fetch')
      ) {
        return {
          type: 'network',
          message: 'Erreur de connexion. Vérifiez votre connexion internet.',
          retryCount: retryCountRef.current,
          maxRetries,
          canRetry: retryCountRef.current < maxRetries,
        };
      }

      // Timeout
      if (msg.toLowerCase().includes('timeout') || err?.code === 'ETIMEDOUT') {
        return {
          type: 'timeout',
          message: 'La requête a pris trop de temps.',
          retryCount: retryCountRef.current,
          maxRetries,
          canRetry: retryCountRef.current < maxRetries,
        };
      }

      // Server
      if (typeof status === 'number' && status >= 500) {
        return {
          type: 'server',
          message: 'Erreur serveur. Veuillez réessayer plus tard.',
          retryCount: retryCountRef.current,
          maxRetries,
          canRetry: retryCountRef.current < maxRetries,
        };
      }

      return {
        type: 'unknown',
        message: msg || 'Une erreur inattendue est survenue.',
        retryCount: retryCountRef.current,
        maxRetries,
        canRetry: retryCountRef.current < maxRetries,
      };
    },
    [maxRetries],
  );

  const clearError = useCallback(() => {
    setError(null);
    retryCountRef.current = 0;
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
  }, []);

  const handleError = useCallback(
    (err: any) => {
      const parsed = parseError(err);
      setError(parsed);

      if (parsed.type === 'quota' && onQuotaExceeded) {
        onQuotaExceeded();
      }

      // Note: le countdown et le trigger de retry automatique sont gérés par le composant UI.
      // Ici on ne fait que préparer l'état.
    },
    [parseError, onQuotaExceeded],
  );

const retry = useCallback(
    async (retryFn: () => Promise<any>) => {
      // Si pas d'erreur, on laisse passer
      if (retryCountRef.current >= maxRetries) {
        setError((prev: ErrorState | null) => (prev ? { ...prev, canRetry: false } : null));
        return;
      }

      retryCountRef.current += 1;
      setError(
        (prev: ErrorState | null) =>
          (prev ? { ...prev, retryCount: retryCountRef.current } : null),
      );


      try {
        await retryFn();
        clearError();
      } catch (err) {
        handleError(err);
      }
    },
    [clearError, handleError, maxRetries],
  );

  return {
    error,
    handleError,
    clearError,
    retry,
  };
}


