import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Briefcase, MapPin, Clock, ChevronRight, Loader2, Search
} from 'lucide-react'
import Card from '../components/ui/Card'

export default function JobsPage() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('/api/v1/jobs', {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setJobs(data.items || [])
      }
    } catch (error) {
      console.error('Error fetching jobs:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredJobs = jobs.filter(job => 
    job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Offres d'emploi</h1>
          <p className="text-dark-400">Trouvez et comparez les offres avec votre CV</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-8">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Rechercher une offre..."
          className="w-full pl-12 pr-4 py-3 bg-dark-800 border border-dark-700 rounded-lg text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Jobs List */}
      <div className="space-y-4">
        {filteredJobs.length === 0 ? (
          <Card className="p-12 text-center">
            <Briefcase className="w-12 h-12 text-dark-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">Aucune offre trouvée</h3>
            <p className="text-dark-400">Les offres apparaîtront ici une fois créées</p>
          </Card>
        ) : (
          filteredJobs.map((job) => (
            <Card 
              key={job.id} 
              className="p-6 hover:border-primary-500/30 transition-all cursor-pointer"
              onClick={() => navigate(`/match/${job.id}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-white">{job.title}</h3>
                    {job.experience_level && (
                      <span className="px-2 py-1 bg-primary-500/10 text-primary-400 rounded text-xs">
                        {job.experience_level}
                      </span>
                    )}
                  </div>
                  
                  {job.company && (
                    <p className="text-dark-300 text-sm mb-2">{job.company}</p>
                  )}
                  
                  <p className="text-dark-400 text-sm line-clamp-2 mb-4">
                    {job.description}
                  </p>
                  
                  <div className="flex flex-wrap items-center gap-4 text-sm text-dark-400">
                    {job.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {job.location}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {new Date(job.created_at).toLocaleDateString('fr-FR')}
                    </span>
                  </div>

                  {job.required_skills?.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {job.required_skills.map((skill, i) => (
                        <span key={i} className="px-2 py-1 bg-dark-700 text-dark-300 rounded text-xs">
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                
                <ChevronRight className="w-5 h-5 text-dark-500 mt-1" />
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}