import { Brain, Github, Linkedin, Twitter } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-dark-900 border-t border-dark-800 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-6 h-6 text-primary-500" />
              <span className="text-lg font-bold gradient-text">CVision AI</span>
            </div>
            <p className="text-dark-400 text-sm max-w-md">
              Plateforme intelligente d'analyse de CV et préparation aux entretiens. 
              Propulsée par l'IA pour vous aider à décrocher le job de vos rêves.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Produit</h3>
            <ul className="space-y-2 text-sm text-dark-400">
              <li><a href="#" className="hover:text-primary-400 transition-colors">Analyse CV</a></li>
              <li><a href="#" className="hover:text-primary-400 transition-colors">Préparation entretien</a></li>
              <li><a href="#" className="hover:text-primary-400 transition-colors">Matching emploi</a></li>
              <li><a href="#" className="hover:text-primary-400 transition-colors">Dashboard</a></li>
            </ul>
          </div>

          {/* Social */}
          <div>
            <h3 className="text-white font-semibold mb-4">Suivez-nous</h3>
            <div className="flex gap-4">
              <a href="#" className="text-dark-400 hover:text-primary-400 transition-colors">
                <Github className="w-5 h-5" />
              </a>
              <a href="#" className="text-dark-400 hover:text-primary-400 transition-colors">
                <Linkedin className="w-5 h-5" />
              </a>
              <a href="#" className="text-dark-400 hover:text-primary-400 transition-colors">
                <Twitter className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="border-t border-dark-800 mt-8 pt-8 text-center text-sm text-dark-500">
          © {new Date().getFullYear()} CVision AI. Tous droits réservés.
        </div>
      </div>
    </footer>
  )
}