import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  FileText, TrendingUp, AlertTriangle, CheckCircle, 
  Lightbulb, Award, Target, ArrowLeft, Loader2 
} from 'lucide-react'
import Card from '../components/ui/Card'
import ScoreChart from '../components/charts/ScoreChart'
import { CVGeminiAnalysis } from '../components/CV/CVGeminiAnalysis'


export default function CVAnalysisPage() {
  const { cvId } = useParams()
  const navigate = useNavigate()
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchAnalysis = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/v1/cvs/${cvId}/analysis`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setAnalysis(data)
      }
    } catch (error) {
      console.error('Error fetching analysis:', error)
    } finally {
      setLoading(false)
    }
  }, [cvId])

  useEffect(() => {
    fetchAnalysis()
  }, [fetchAnalysis])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (!analysis) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Analyse non trouvée</h2>
        <button onClick={() => navigate('/upload-cv')} className="btn-primary mt-4">
          Analyser un CV
        </button>
      </div>
    )
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-amber-400'
    return 'text-red-400'
  }

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-green-500/10 border-green-500/20'
    if (score >= 60) return 'bg-amber-500/10 border-amber-500/20'
    return 'bg-red-500/10 border-red-500/20'
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Header */}
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-dark-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour au dashboard
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Analyse de votre CV</h1>
        <p className="text-dark-400">Résultats détaillés de l'analyse IA</p>
      </div>

      {/* Score Overview */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <Card className="lg:col-span-1">

          <h3 className="text-lg font-semibold mb-4 text-center">Score Global</h3>
          <div className="text-center py-4">
            <div className={`text-6xl font-bold ${getScoreColor(analysis.overall_score)}`}>
              {analysis.overall_score}
            </div>
            <div className="text-dark-400 mt-2">sur 100</div>
          </div>
          <div className={`p-3 rounded-lg text-center text-sm ${getScoreBg(analysis.overall_score)}`}>
            {analysis.overall_score >= 80 ? 'Excellent CV !' : 
             analysis.overall_score >= 60 ? 'Bon CV, quelques améliorations possibles' : 
             'CV à optimiser significativement'}
          </div>
        </Card>

        <Card className="lg:col-span-1">
          <h3 className="text-lg font-semibold mb-4">Répartition des scores</h3>
          <ScoreChart 
            structure={analysis.structure_score}
            content={analysis.content_score}
            keywords={analysis.keywords_score}
            overall={analysis.overall_score}
          />
        </Card>

        <div className="lg:col-span-1">
          <CVGeminiAnalysis cvId={cvId} />
        </div>
      </div>


      {/* Detailed Scores */}
      <div className="grid md:grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Structure', score: analysis.structure_score, icon: FileText },
          { label: 'Contenu', score: analysis.content_score, icon: TrendingUp },
          { label: 'Mots-clés', score: analysis.keywords_score, icon: Target },
        ].map((item, i) => (
          <Card key={i} className="text-center">
            <item.icon className={`w-8 h-8 mx-auto mb-2 ${getScoreColor(item.score)}`} />
            <div className={`text-2xl font-bold ${getScoreColor(item.score)}`}>{item.score}</div>
            <div className="text-sm text-dark-400">{item.label}</div>
          </Card>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Skills */}
        <Card>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-primary-500" />
            Compétences détectées ({analysis.detected_skills?.length || 0})
          </h3>
          <div className="flex flex-wrap gap-2">
            {analysis.detected_skills?.map((skill, i) => (
              <span key={i} className="px-3 py-1 bg-primary-500/10 text-primary-400 rounded-full text-sm">
                {skill}
              </span>
            )) || <span className="text-dark-400">Aucune compétence détectée</span>}
          </div>

          {analysis.missing_skills?.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-dark-300 mb-2">Compétences tendance manquantes</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.missing_skills.map((skill, i) => (
                  <span key={i} className="px-3 py-1 bg-amber-500/10 text-amber-400 rounded-full text-sm">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Card>

        {/* Strengths & Weaknesses */}
        <div className="space-y-4">
          <Card>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              Points forts
            </h3>
            <ul className="space-y-3">
              {analysis.strengths?.map((strength, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                  <span className="text-dark-200">{strength}</span>
                </li>
              )) || <li className="text-dark-400">Aucun point fort identifié</li>}
            </ul>
          </Card>

          <Card>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              Points à améliorer
            </h3>
            <ul className="space-y-3">
              {analysis.weaknesses?.map((weakness, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                  <span className="text-dark-200">{weakness}</span>
                </li>
              )) || <li className="text-dark-400">Aucun point faible identifié</li>}
            </ul>
          </Card>
        </div>
      </div>

      {/* Recommendations */}
      <Card className="mt-8">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-primary-500" />
          Recommandations personnalisées
        </h3>
        <div className="grid md:grid-cols-2 gap-4">
          {analysis.recommendations?.map((rec, i) => (
            <div key={i} className="flex items-start gap-3 p-4 bg-dark-800/50 rounded-lg">
              <div className="w-8 h-8 bg-primary-500/10 rounded-lg flex items-center justify-center shrink-0">
                <span className="text-primary-400 font-bold text-sm">{i + 1}</span>
              </div>
              <p className="text-sm text-dark-200">{rec}</p>
            </div>
          )) || <p className="text-dark-400 col-span-2">Aucune recommandation</p>}
        </div>
      </Card>
    </div>
  )
}