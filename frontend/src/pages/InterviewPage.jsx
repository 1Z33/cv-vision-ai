import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  MessageSquare, Send, Loader2, Clock,
  CheckCircle, AlertCircle, Brain 
} from 'lucide-react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

import VocalInterviewPanel from '../components/VocalInterviewPanel'
import GeminiNotice from '../components/GeminiNotice'

import { ErrorHandler } from '../components/ErrorHandler'
import { useErrorHandler } from '../hooks/useErrorHandler'



export default function InterviewPage() {
  const [answerMode, setAnswerMode] = useState('text') // 'text' | 'vocal'

  const navigate = useNavigate()
  const [step, setStep] = useState('setup') // setup | active | loading
  const [sessionId, setSessionId] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [geminiNotice, setGeminiNotice] = useState(null)

  const [loading, setLoading] = useState(false)
  const [difficulty, setDifficulty] = useState('medium')
  const [jobTitle, setJobTitle] = useState('')

  const { error, handleError, clearError, retry } = useErrorHandler({
    maxRetries: 3,
    onQuotaExceeded: () => {
      fetch('/api/v1/report-quota', { method: 'POST' })
    },
  })



  const startInterview = async () => {
    setLoading(true)
    clearError()

    try {

      const token = localStorage.getItem('access_token')
      const response = await fetch('/api/v1/interviews/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          difficulty,
          job_title: jobTitle || undefined,
        }),
      })

      if (!response.ok) {
        const err = await response.json().catch(() => null)
        const detail = err?.detail || `HTTP ${response.status}`
        throw new Error(detail)
      }

      const data = await response.json()
      setSessionId(data.session_id)
      setCurrentQuestion({
        number: data.question_number,
        text: data.question_text,
        type: data.question_type,
      })
      setStep('active')
      // Source de génération / fallback => notice dédiée
      if (data?.source === 'fallback' || data?.fallback_reason) {
        setGeminiNotice({
          source: data?.source,
          fallbackReason: data?.fallback_reason,
        })
      } else {
        setGeminiNotice(null)
      }
    } catch (error) {
      handleError(error)
      console.error('Error starting interview:', error)
    } finally {
      setLoading(false)
    }
  }


  const submitAnswer = async () => {
    if (!answer.trim()) return

    setLoading(true)
    clearError()
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/v1/interviews/${sessionId}/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ answer }),
      })

      if (!response.ok) {
        const err = await response.json().catch(() => null)
        const detail = err?.detail || `HTTP ${response.status}`
        throw new Error(detail)
      }

      const data = await response.json()
      setFeedback(data)
      setAnswer('')

      if (data.is_complete) {
        setTimeout(() => {
          navigate(`/interview-feedback/${sessionId}`)
        }, 3000)
      } else if (data.next_question) {
        // garder la notice, mais refresh du feedback
        setCurrentQuestion({
          number: data.question_number + 1,
          text: data.next_question,
          type: currentQuestion?.type,
        })
        setFeedback(null)
      }
    } catch (error) {
      const type = inferErrorType(error) || 'network'

      if (type === 'quota') {
        showRetryBanner('quota', {
          title: 'Quota token atteint',
          detail: 'Limite d’utilisation atteinte. Réessayez plus tard.',
          actionLabel: 'Réessayer',
          onAction: () => submitAnswer(),
        })
      } else {
        showRetryBanner('network', {
          title: 'Problème de connexion',
          detail: 'La demande a échoué. Vérifiez votre connexion et réessayez.',
          actionLabel: 'Réessayer',
          onAction: () => submitAnswer(),
        })
      }

      console.error('Error submitting answer:', error)
    } finally {
      setLoading(false)
    }
  }


  if (step === 'setup') {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 animate-fade-in">
        <div className="text-center mb-8">
          <Brain className="w-12 h-12 text-primary-500 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-white mb-2">Simulateur d'entretien IA</h1>
          <p className="text-dark-400">
            Pratiquez avec des questions générées par notre IA et recevez un feedback instantané
          </p>
        </div>

        <Card className="p-8 space-y-6">
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">
              Poste visé (optionnel)
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="ex: Développeur Full Stack"
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-3">
              Niveau de difficulté
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: 'easy', label: 'Facile', desc: 'Questions générales' },
                { value: 'medium', label: 'Moyen', desc: 'Questions techniques' },
                { value: 'hard', label: 'Difficile', desc: 'Scénarios complexes' },
              ].map((level) => (
                <button
                  key={level.value}
                  onClick={() => setDifficulty(level.value)}
                  className={`
                    p-4 rounded-lg border text-left transition-all
                    ${difficulty === level.value
                      ? 'border-primary-500 bg-primary-500/10 text-white'
                      : 'border-dark-700 text-dark-400 hover:border-dark-600'
                    }
                  `}
                >
                  <div className="font-medium mb-1">{level.label}</div>
                  <div className="text-xs opacity-70">{level.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <Button
            onClick={startInterview}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Préparation...
              </>
            ) : (
              <>
                <MessageSquare className="w-5 h-5 mr-2" />
                Démarrer l'entretien
              </>
            )}
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 animate-fade-in">
      <ErrorHandler
        error={error}
        onRetry={() => retry(() => Promise.resolve(startInterview()))}
        onDismiss={clearError}
        onReportQuota={() => fetch('/api/v1/report-quota', { method: 'POST' })}
      />


      {/* Progress */}
      <div className="mb-6">

        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-dark-400">
            Question {currentQuestion?.number || 1}/5
          </span>
          <span className="text-sm text-dark-400 flex items-center gap-1">
            <Clock className="w-4 h-4" />
            Prenez votre temps
          </span>
        </div>
        <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-500 transition-all duration-500"
            style={{ width: `${((currentQuestion?.number || 1) / 5) * 100}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <Card className="p-8 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <span
            className={`
              px-3 py-1 rounded-full text-xs font-medium
              ${
                currentQuestion?.type === 'technical'
                  ? 'bg-blue-500/10 text-blue-400'
                  : currentQuestion?.type === 'behavioral'
                    ? 'bg-purple-500/10 text-purple-400'
                    : 'bg-amber-500/10 text-amber-400'
              }
            `}
          >
            {currentQuestion?.type === 'technical'
              ? 'Technique'
              : currentQuestion?.type === 'behavioral'
                ? 'Comportementale'
                : 'Situationnelle'}
          </span>
        </div>
        <h2 className="text-xl font-semibold text-white leading-relaxed">
          {currentQuestion?.text}
        </h2>
      </Card>

      {/* Notice Gemini fallback (déduite du start) */}
      {geminiNotice?.source === 'fallback' && (
        <div className="mb-6">
          <GeminiNotice
            fallbackReason={geminiNotice?.fallbackReason}
            message="Gemini indisponible — mode analyse locale active"
          />
        </div>
      )}

      {/* Feedback */}
      {feedback && (

        <Card
          className={`p-6 mb-6 ${feedback.answer_score >= 70 ? 'border-green-500/30' : 'border-amber-500/30'}`}
        >

          <div className="flex items-center gap-3 mb-3">
            {feedback.answer_score >= 70 ? (
              <CheckCircle className="w-6 h-6 text-green-500" />
            ) : (
              <AlertCircle className="w-6 h-6 text-amber-500" />
            )}
            <span
              className={`text-lg font-bold ${feedback.answer_score >= 70 ? 'text-green-400' : 'text-amber-400'}`}
            >
              Score: {feedback.answer_score}/100
            </span>
          </div>
          <p className="text-dark-200 text-sm leading-relaxed">{feedback.feedback_text}</p>
          {feedback.detected_keywords?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {feedback.detected_keywords.map((kw, i) => (
                <span key={i} className="px-2 py-1 bg-green-500/10 text-green-400 rounded text-xs">
                  ✓ {kw}
                </span>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Answer Input */}
      {!feedback?.is_complete && (
        <div className="space-y-4">
          {/* Toggle Texte / Vocal */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setAnswerMode('text')}
              className={`px-4 py-2 rounded-lg border transition-all ${
                answerMode === 'text'
                  ? 'border-primary-500 bg-primary-500/10 text-white'
                  : 'border-dark-700 text-dark-400 hover:border-dark-600'
              }`}
            >
              ✏️ Texte
            </button>
            <button
              type="button"
              onClick={() => setAnswerMode('vocal')}
              className={`px-4 py-2 rounded-lg border transition-all ${
                answerMode === 'vocal'
                  ? 'border-primary-500 bg-primary-500/10 text-white'
                  : 'border-dark-700 text-dark-400 hover:border-dark-600'
              }`}
            >
              🎙️ Vocal
            </button>
          </div>

          {answerMode === 'vocal' && (
            <VocalInterviewPanel 
              sessionId={sessionId} 
              onTranscriptChange={setAnswer}
              isEmbedded={true}
            />
          )}

          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Rédigez votre réponse ici (ou utilisez le mode vocal)..."
            rows={6}
            className="w-full px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          />

          <div className="flex justify-end">
            <Button
              onClick={submitAnswer}
              disabled={!answer.trim() || loading}
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Évaluation...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5 mr-2" />
                  Soumettre la réponse
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {feedback?.is_complete && (
        <Card className="p-6 text-center border-green-500/30">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
          <h3 className="text-xl font-bold text-white mb-2">Entretien terminé !</h3>
          <p className="text-dark-400">Redirection vers le feedback global...</p>
        </Card>
      )}
    </div>
  )
}
