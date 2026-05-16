import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Trophy, TrendingUp, CheckCircle, AlertTriangle, 
  ArrowLeft, Loader2, Target, Star 
} from 'lucide-react'
import Card from '../components/ui/Card'

export default function InterviewFeedbackPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [feedback, setFeedback] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchFeedback = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/v1/interviews/${sessionId}/feedback`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setFeedback(data)
      }
    } catch (error) {
      console.error('Error fetching feedback:', error)
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    fetchFeedback()
  }, [fetchFeedback])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (!feedback) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 text-center">
        <h2 className="text-xl font-bold text-white mb-4">Feedback non disponible</h2>
        <button onClick={() => navigate('/interview')} className="btn-primary">
          Nouvel entretien
        </button>
      </div>
    )
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-amber-400'
    return 'text-red-400'
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-dark-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour au dashboard
      </button>

      {/* Header */}
      <div className="text-center mb-8">
        <Trophy className="w-16 h-16 text-primary-500 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-white mb-2">Résultats de l'entretien</h1>
        <p className="text-dark-400">Voici le feedback détaillé de votre simulation</p>
      </div>

      {/* Overall Score */}
      <Card className="p-8 mb-8 text-center">
        <div className={`text-7xl font-bold ${getScoreColor(feedback.total_score)} mb-2`}>
          {feedback.total_score}
        </div>
        <div className="text-dark-400 mb-4">Score global sur 100</div>
        <p className="text-lg text-dark-200 max-w-2xl mx-auto">{feedback.general_feedback}</p>
      </Card>

      {/* Summary */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <Card>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Star className="w-5 h-5 text-green-500" />
            Points forts
          </h3>
          <ul className="space-y-3">
            {feedback.strengths?.map((strength, i) => (
              <li key={i} className="flex items-start gap-3 text-sm">
                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                <span className="text-dark-200">{strength}</span>
              </li>
            )) || <li className="text-dark-400">Aucun point fort identifié</li>}
          </ul>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-amber-500" />
            Axes d'amélioration
          </h3>
          <ul className="space-y-3">
            {feedback.areas_to_improve?.map((area, i) => (
              <li key={i} className="flex items-start gap-3 text-sm">
                <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                <span className="text-dark-200">{area}</span>
              </li>
            )) || <li className="text-dark-400">Aucun axe d'amélioration identifié</li>}
          </ul>
        </Card>
      </div>

      {/* Detailed Answers */}
      <h3 className="text-xl font-semibold mb-4">Détail des réponses</h3>
      <div className="space-y-4">
        {feedback.answers_summary?.map((qa, i) => (
          <Card key={i} className="p-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-dark-400">Question {qa.question_number}</span>
              <span className={`text-lg font-bold ${getScoreColor(qa.answer_score)}`}>
                {qa.answer_score}/100
              </span>
            </div>
            <p className="text-white font-medium mb-3">{qa.question_text}</p>
            <p className="text-sm text-dark-400 mb-3">{qa.feedback_text}</p>
            {qa.detected_keywords?.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {qa.detected_keywords.map((kw, j) => (
                  <span key={j} className="px-2 py-1 bg-green-500/10 text-green-400 rounded text-xs">
                    ✓ {kw}
                  </span>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* CTA */}
      <div className="mt-8 text-center">
        <button
          onClick={() => navigate('/interview')}
          className="btn-primary inline-flex items-center gap-2"
        >
          <TrendingUp className="w-5 h-5" />
          Refaire un entretien
        </button>
      </div>
    </div>
  )
}