import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { 
  FileText, MessageSquare, Target, TrendingUp, 
  Award, Clock, ChevronRight 
} from 'lucide-react'

import Card from '../components/ui/Card'
import ScoreChart from '../components/charts/ScoreChart'
import ProgressChart from '../components/charts/ProgressChart'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuthStore()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, navigate])

  if (!isAuthenticated) return null

  // Données de démo (à remplacer par des appels API)
  const stats = {
    avgScore: 78,
    totalCVs: 5,
    totalInterviews: 3,
    totalMatches: 8,
  }

  const [recentCVs, setRecentCVs] = useState([])
  const [loadingRecentCVs, setLoadingRecentCVs] = useState(true)


  useEffect(() => {
    let isMounted = true

    async function loadRecentCVs() {
      try {
        setLoadingRecentCVs(true)
        const token = localStorage.getItem('access_token')

        const res = await fetch('/api/v1/cvs', {
          headers: {
            Authorization: token ? `Bearer ${token}` : '',
          },
        })

        if (!res.ok) throw new Error(`Failed to fetch recent CVs: ${res.status}`)
        const data = await res.json()

        const items = Array.isArray(data?.items) ? data.items : []

        // Prend les 5 derniers CV (supposition: l'API renvoie déjà triés)
        const last = items.slice(-5).reverse()

        // Mapper la réponse API vers la structure attendue par l'UI
        const mapped = last.map((cv) => ({
          id: cv.id,
          name: cv.filename || cv.name || 'CV',
          score: cv.score ?? cv.overall_score ?? cv.avg_score ?? 0,
          date: cv.created_at || cv.uploaded_at || cv.date || '',
        }))

        if (isMounted) setRecentCVs(mapped)
      } catch (e) {
        if (isMounted) setRecentCVs([])
      } finally {
        if (isMounted) setLoadingRecentCVs(false)
      }
    }

    loadRecentCVs()

    return () => {
      isMounted = false
    }
  }, [])




  const progressData = [
    { date: 'Jan', score: 65 },
    { date: 'Fév', score: 72 },
    { date: 'Mar', score: 78 },
    { date: 'Avr', score: 82 },
    { date: 'Mai', score: 85 },
  ]

  const quickActions = [
    { 
      icon: FileText, 
      label: 'Analyser un CV', 
      description: 'Upload et analyse IA',
      to: '/upload-cv',
      color: 'text-primary-400 bg-primary-500/10'
    },
    { 
      icon: MessageSquare, 
      label: 'Simuler entretien', 
      description: 'Questions générées par IA',
      to: '/interview',
      color: 'text-green-400 bg-green-500/10'
    },
    { 
      icon: Target, 
      label: 'Matcher offres', 
      description: 'Trouvez le job parfait',
      to: '/jobs',
      color: 'text-amber-400 bg-amber-500/10'
    },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Bonjour, {user?.full_name || 'Candidat'} ! 👋
        </h1>
        <p className="text-dark-400">Voici un aperçu de votre progression</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card className="text-center">
          <div className="text-3xl font-bold text-primary-400 mb-1">{stats.avgScore}</div>
          <div className="text-sm text-dark-400">Score moyen</div>
        </Card>
        <Card className="text-center">
          <div className="text-3xl font-bold text-green-400 mb-1">{stats.totalCVs}</div>
          <div className="text-sm text-dark-400">CVs analysés</div>
        </Card>
        <Card className="text-center">
          <div className="text-3xl font-bold text-amber-400 mb-1">{stats.totalInterviews}</div>
          <div className="text-sm text-dark-400">Entretiens</div>
        </Card>
        <Card className="text-center">
          <div className="text-3xl font-bold text-purple-400 mb-1">{stats.totalMatches}</div>
          <div className="text-sm text-dark-400">Matchs</div>
        </Card>
      </div>

      <div className="grid lg:grid-cols-3 gap-8 mb-8">
        {/* Score Chart */}
        <Card>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-primary-500" />
            Dernier score
          </h3>
          <ScoreChart 
            structure={85} 
            content={78} 
            keywords={72} 
            overall={78} 
          />
        </Card>

        {/* Progress Chart */}
        <Card className="lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-500" />
            Progression
          </h3>
          <ProgressChart data={progressData} />
        </Card>
      </div>

      {/* Quick Actions */}
      <h3 className="text-lg font-semibold mb-4">Actions rapides</h3>
      <div className="grid md:grid-cols-3 gap-4 mb-8">
        {quickActions.map((action, index) => (
          <button
            key={index}
            onClick={() => navigate(action.to)}
            className="glass-card p-6 text-left hover:border-primary-500/30 transition-all group"
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${action.color}`}>
              <action.icon className="w-6 h-6" />
            </div>
            <h4 className="font-semibold text-white mb-1 group-hover:text-primary-400 transition-colors">
              {action.label}
            </h4>
            <p className="text-sm text-dark-400">{action.description}</p>
          </button>
        ))}
      </div>

      {/* Recent CVs */}
      <h3 className="text-lg font-semibold mb-4">CVs récents</h3>
      <div className="space-y-3">
        {recentCVs.map((cv) => (
          <div
            key={cv.id}
            onClick={() => navigate(`/cv-analysis/${cv.id}`)}
            className="glass-card p-4 flex items-center justify-between cursor-pointer hover:border-primary-500/30 transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-primary-500/10 rounded-lg flex items-center justify-center">
                <FileText className="w-5 h-5 text-primary-500" />
              </div>
              <div>
                <h4 className="font-medium text-white">{cv.name}</h4>
                <p className="text-sm text-dark-400 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {cv.date}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-lg font-bold text-primary-400">{cv.score}/100</div>
                <div className="text-xs text-dark-400">Score</div>
              </div>
              <ChevronRight className="w-5 h-5 text-dark-500" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}