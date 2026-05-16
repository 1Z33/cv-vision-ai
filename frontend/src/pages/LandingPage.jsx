import { Link } from 'react-router-dom'
import { FileText, MessageSquare, Target, ArrowRight, CheckCircle, Star, Users } from 'lucide-react'

export default function LandingPage() {
  const features = [
    {
      icon: FileText,
      title: 'Analyse de CV IA',
      description: 'Uploadez votre CV en PDF et recevez une analyse détaillée avec score sur 100, compétences détectées et recommandations personnalisées.'
    },
    {
      icon: MessageSquare,
      title: 'Préparation Entretien',
      description: 'Simulez des entretiens d\'embauche réalistes avec questions générées par IA et feedback instantané sur vos réponses.'
    },
    {
      icon: Target,
      title: 'Matching Emploi',
      description: 'Comparez votre CV avec des offres d\'emploi et découvrez votre taux de compatibilité ainsi que les compétences à développer.'
    }
  ]

  const stats = [
    { value: '10K+', label: 'CVs analysés' },
    { value: '95%', label: 'Satisfaction' },
    { value: '500+', label: 'Questions générées' },
    { value: '50+', label: 'Offres matchées' },
  ]

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-900/20 to-transparent" />
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-full text-primary-400 text-sm mb-8">
            <Star className="w-4 h-4" />
            Propulsé par l'Intelligence Artificielle
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Optimisez votre <span className="gradient-text">carrière</span>
            <br />avec l'IA
          </h1>
          
          <p className="text-xl text-dark-400 max-w-2xl mx-auto mb-10">
            Analysez votre CV, préparez vos entretiens et trouvez le job parfait 
            grâce à notre plateforme intelligente.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register" className="btn-primary inline-flex items-center gap-2 justify-center">
              Commencer gratuitement
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/login" className="btn-secondary inline-flex items-center gap-2 justify-center">
              J'ai déjà un compte
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 border-y border-dark-800 bg-dark-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-white mb-2">{stat.value}</div>
                <div className="text-dark-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Tout ce dont vous avez besoin</h2>
            <p className="text-dark-400 max-w-2xl mx-auto">
              Une suite complète d'outils pour chaque étape de votre recherche d'emploi
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="glass-card p-8 hover:border-primary-500/30 transition-all duration-300 group">
                <div className="w-14 h-14 bg-primary-500/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-primary-500/20 transition-colors">
                  <feature.icon className="w-7 h-7 text-primary-500" />
                </div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-dark-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-900/30 to-primary-600/10" />
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <Users className="w-12 h-12 text-primary-500 mx-auto mb-6" />
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Prêt à booster votre carrière ?
          </h2>
          <p className="text-dark-400 text-lg mb-8 max-w-2xl mx-auto">
            Rejoignez des milliers de candidats qui ont déjà amélioré leur CV 
            et décroché leur emploi de rêve.
          </p>
          <Link to="/register" className="btn-primary inline-flex items-center gap-2">
            Créer mon compte
            <ArrowRight className="w-5 h-5" />
          </Link>
          
          <div className="mt-8 flex items-center justify-center gap-6 text-sm text-dark-400">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-primary-500" />
              Gratuit
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-primary-500" />
              Sans engagement
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-primary-500" />
              IA avancée
            </span>
          </div>
        </div>
      </section>
    </div>
  )
}