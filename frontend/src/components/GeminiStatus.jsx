import React, { useEffect, useState } from 'react';
import api from '../services/api';

export const GeminiStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const res = await api.get('/gemini-status');

      setStatus(res.data);
    } catch (err) {
      setStatus({ enabled: false, model: null });
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-500">⏳ ...</span>
    );
  }

  if (!status?.enabled) {
    return (
      <span className="px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-600">⚠️ IA offline</span>
    );
  }

  return (
    <span className="px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-700">⚡ Gemini {status.model}</span>
  );
};

