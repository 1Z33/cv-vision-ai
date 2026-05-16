import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Target, ArrowLeft, CheckCircle, XCircle, Loader2,
  AlertTriangle, Award 
} from 'lucide-react'
import Card from '../components/ui/Card'

export default function MatchResultPage() {
  const { cvId } = useParams()
  const navigate = useNavigate()
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchMatches = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`/api/v1/matches/${cvId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setMatches(data || [])
      }
    } catch (error) {
      console.error('Error fetching matches:', error)
    } finally {
      setLoading(false)
    }
  }, [cvId])

  useEffect(() => {
    fetchMatches()
  }, [fetchMatches])

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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <button
        onClick={() => navigate('/jobs')}
        className="flex items-center gap-2 text-dark-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour aux offres
      </button>

      <div className="text-center mb-8">
        <Target className="w-12 h-12 text-primary-500 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-white mb-2">Résultats du matching</h1>
        <p className="text-dark-400">Compatibilité de votre CV avec les offres</p>
      </div>

      {matches.length === 0 ? (
        <Card className="p-12 text-center">
          <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">Aucun match trouvé</h3>
          <p className="text-dark-400 mb-4">Lancez un matching depuis la page des offres</p>
          <button onClick={() => navigate('/jobs')} className="btn-primary">
            Voir les offres
          </button>
        </Card>
      ) : (
        <div className="space-y-6">
          {matches.map((match, index) => (
            <Card key={index} className={`p-6 ${getScoreBg(match.compatibility_score)}`}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-1">{match.job_title}</h3>
                  <div className={`text-3xl font-bold ${getScoreColor(match.compatibility_score)}`}>
                    {match.compatibility_score}%
                  </div>
                </div>
                <Award className={`w-8 h-8 ${getScoreColor(match.compatibility_score)}`} />
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-dark-300 mb-3 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    Compétences matchées ({match.matching_skills_count})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {match.matching_skills?.map((skill, i) => (
                      <span key={i} className="px-2 py-1 bg-green-500/10 text-green-400 rounded text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-dark-300 mb-3 flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-red-500" />
                    Compétences manquantes ({match.missing_skills_count})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {match.missing_skills?.map((skill, i) => (
                      <span key={i} className="px-2 py-1 bg-red-500/10 text-red-400 rounded text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}