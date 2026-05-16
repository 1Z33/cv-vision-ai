export const APP_NAME = 'CVision AI'
export const APP_VERSION = '1.0.0'

export const DIFFICULTY_LEVELS = {
  easy: { label: 'Facile', color: 'text-green-400', bg: 'bg-green-500/10' },
  medium: { label: 'Moyen', color: 'text-amber-400', bg: 'bg-amber-500/10' },
  hard: { label: 'Difficile', color: 'text-red-400', bg: 'bg-red-500/10' },
}

export const QUESTION_TYPES = {
  technical: { label: 'Technique', color: 'text-blue-400', bg: 'bg-blue-500/10' },
  behavioral: { label: 'Comportementale', color: 'text-purple-400', bg: 'bg-purple-500/10' },
  situational: { label: 'Situationnelle', color: 'text-amber-400', bg: 'bg-amber-500/10' },
}

export const MAX_FILE_SIZE = 5 * 1024 * 1024 // 5MB
export const ACCEPTED_FILE_TYPES = ['application/pdf']