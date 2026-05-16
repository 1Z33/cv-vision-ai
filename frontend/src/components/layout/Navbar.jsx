import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { Brain, Menu, X, LogOut, User, FileText, MessageSquare, Briefcase, LayoutDashboard } from 'lucide-react'
import { useState } from 'react'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const navLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/upload-cv', label: 'Analyser CV', icon: FileText },
    { to: '/interview', label: 'Entretien', icon: MessageSquare },
    { to: '/jobs', label: 'Offres', icon: Briefcase },
  ]

  return (
    <nav className="sticky top-0 z-50 bg-dark-900/80 backdrop-blur-xl border-b border-dark-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <Brain className="w-8 h-8 text-primary-500 group-hover:text-primary-400 transition-colors" />
            <span className="text-xl font-bold gradient-text">CVision AI</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {isAuthenticated && navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="flex items-center gap-2 px-4 py-2 text-dark-300 hover:text-white hover:bg-dark-800 rounded-lg transition-all"
              >
                <link.icon className="w-4 h-4" />
                {link.label}
              </Link>
            ))}
          </div>

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <span className="text-sm text-dark-400 flex items-center gap-2">
                  <User className="w-4 h-4" />
                  {user?.full_name || user?.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-4 py-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  Déconnexion
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  to="/login"
                  className="px-4 py-2 text-dark-300 hover:text-white transition-colors"
                >
                  Connexion
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-all"
                >
                  S'inscrire
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 text-dark-300 hover:text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-dark-900 border-t border-dark-800">
          <div className="px-4 py-3 space-y-1">
            {isAuthenticated && navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="flex items-center gap-2 px-4 py-3 text-dark-300 hover:text-white hover:bg-dark-800 rounded-lg"
                onClick={() => setMobileMenuOpen(false)}
              >
                <link.icon className="w-5 h-5" />
                {link.label}
              </Link>
            ))}
            {isAuthenticated ? (
              <button
                onClick={() => {
                  handleLogout()
                  setMobileMenuOpen(false)
                }}
                className="flex items-center gap-2 w-full px-4 py-3 text-red-400 hover:bg-red-500/10 rounded-lg"
              >
                <LogOut className="w-5 h-5" />
                Déconnexion
              </button>
            ) : (
              <div className="space-y-2 pt-2">
                <Link
                  to="/login"
                  className="block px-4 py-3 text-dark-300 hover:bg-dark-800 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Connexion
                </Link>
                <Link
                  to="/register"
                  className="block px-4 py-3 bg-primary-600 text-white rounded-lg text-center"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  S'inscrire
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}