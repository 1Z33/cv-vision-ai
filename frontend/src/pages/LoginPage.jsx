import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { LogIn, Eye, EyeOff, Brain } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

const loginSchema = z.object({
  email: z.string().email('Email invalide'),
  password: z.string().min(1, 'Mot de passe requis'),
})

export default function LoginPage() {
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data) => {
    try {
      setError('')
      await login(data.email, data.password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur de connexion')
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Brain className="w-12 h-12 text-primary-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Connexion</h1>
          <p className="text-dark-400">Bienvenue sur CVision AI</p>
        </div>

        {/* Form */}
        <div className="glass-card p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <Input
                label="Email"
                type="email"
                placeholder="votre@email.com"
                {...register('email')}
                error={errors.email?.message}
              />
            </div>

            <div className="relative">
              <Input
                label="Mot de passe"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                {...register('password')}
                error={errors.password?.message}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[38px] text-dark-400 hover:text-white"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                'Connexion...'
              ) : (
                <>
                  <LogIn className="w-5 h-5 mr-2" />
                  Se connecter
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-dark-400 text-sm">
              Pas encore de compte ?{' '}
              <Link to="/register" className="text-primary-400 hover:text-primary-300 transition-colors">
                S'inscrire
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}