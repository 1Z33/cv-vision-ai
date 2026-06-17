export type LiveSessionStatus =
  | 'idle'
  | 'connecting'
  | 'active'
  | 'listening'
  | 'speaking'
  | 'evaluating'
  | 'completed'
  | 'error';

export type LiveMessageEvent =
  | 'session_started'
  | 'question'
  | 'analysis'
  | 'next_question'
  | 'session_finished'
  | 'error'
  | string;

export type InterviewLiveEventMessage = {
  event: LiveMessageEvent;
  payload?: any;
};

export type LiveQuestionPayload = {
  question_text?: string;
  question?: {
    question_text?: string;
    question_number?: number;
  };
  question_number?: number;
  audio_url?: string;
  audio?: {
    url?: string;
  };
};

export type LiveAnalysisPayload = {
  score?: number;
  feedback?: string;
  feedback_text?: string;
  scores?: Record<string, number>;
};

export type LiveNextQuestionPayload = {
  question_text?: string;
  next_question_text?: string;
  question?: {
    question_text?: string;
    question_number?: number;
  };
  next_question_number?: number;
  audio_url?: string;
};

export type ChatTurn = {
  id: string;
  role: 'user' | 'ai' | 'system';
  text: string;
  timestamp: number;
};

