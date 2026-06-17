import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, RefreshCw, WifiOff, Clock, X } from 'lucide-react';

export interface ErrorState {
  type: 'network' | 'quota' | 'server' | 'timeout' | 'unknown';
  message: string;
  retryCount: number;
  maxRetries: number;
  canRetry: boolean;
  retryAfter?: number;
}

interface ErrorHandlerProps {
  error: ErrorState | null;
  onRetry: () => void;
  onDismiss: () => void;
  onReportQuota?: () => void;
}

export const ErrorHandler: React.FC<ErrorHandlerProps> = ({
  error,
  onRetry,
  onDismiss,
  onReportQuota,
}) => {
  const [countdown, setCountdown] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = useCallback(async () => {
    if (isRetrying) return;
    setIsRetrying(true);
    try {
      onRetry();
    } finally {
      setIsRetrying(false);
    }
  }, [isRetrying, onRetry]);

  // Countdown pour retry automatique
  useEffect(() => {
    if (error?.retryAfter && error.retryAfter > 0) {
      setCountdown(error.retryAfter);
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
    setCountdown(0);
  }, [error?.retryAfter]);

  // Retry automatique quand countdown atteint 0
  useEffect(() => {
    if (countdown === 0 && error?.canRetry && !isRetrying) {
      handleRetry();
    }
  }, [countdown, error?.canRetry, isRetrying, handleRetry]);

  if (!error) return null;

  const configByType = {
    quota: {
      icon: <Clock className="h-6 w-6 text-amber-600" />,
      bg: 'bg-amber-50',
      border: 'border-amber-500',
      title: 'Quota API épuisé',
    },
    network: {
      icon: <WifiOff className="h-6 w-6 text-red-600" />,
      bg: 'bg-red-50',
      border: 'border-red-500',
      title: 'Erreur de connexion',
    },
    timeout: {
      icon: <Clock className="h-6 w-6 text-orange-600" />,
      bg: 'bg-orange-50',
      border: 'border-orange-500',
      title: 'Délai dépassé',
    },
    server: {
      icon: <AlertTriangle className="h-6 w-6 text-red-600" />,
      bg: 'bg-red-50',
      border: 'border-red-500',
      title: 'Erreur serveur',
    },
    unknown: {
      icon: <AlertTriangle className="h-6 w-6 text-gray-600" />,
      bg: 'bg-gray-50',
      border: 'border-gray-500',
      title: 'Erreur',
    },
  } as const;

  const config = configByType[error.type] || configByType.unknown;

  return (
    <div className={`${config.bg} border-l-4 ${config.border} p-4 mb-4 rounded-r-lg shadow-sm`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">{config.icon}</div>
        <div className="flex-1">
          <div className="flex items-start justify-between gap-3">
            <h3 className="font-semibold text-gray-900">{config.title}</h3>
            <button
              type="button"
              onClick={onDismiss}
              className="p-1 rounded text-gray-500 hover:text-gray-700"
              aria-label="Fermer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <p className="text-sm text-gray-700 mt-1">{error.message}</p>

          {error.retryCount > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              Tentative {error.retryCount}/{error.maxRetries}
            </p>
          )}

          {countdown > 0 && (
            <p className="text-sm text-amber-700 mt-2">
              <Clock className="h-4 w-4 inline mr-1" />
              Réessai automatique dans {countdown}s
            </p>
          )}

          <div className="flex flex-wrap gap-2 mt-3">
            {error.type === 'quota' && onReportQuota && (
              <button
                type="button"
                onClick={onReportQuota}
                className="px-3 py-1.5 rounded text-sm font-medium bg-amber-600 hover:bg-amber-700 text-white"
              >
                Signaler le problème
              </button>
            )}

            {error.canRetry && (
              <button
                type="button"
                onClick={handleRetry}
                disabled={isRetrying}
                className="flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isRetrying ? 'animate-spin' : ''}`} />
                Réessayer
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorHandler;

