import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { UserPlus, Eye, EyeOff, Brain } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

const registerSchema = z.object({
  full_name: z.string().min(2, 'Nom trop court').max(100, 'Nom trop long'),
  email: z.string().email('Email invalide'),
  password: z.string().min(8, 'Minimum 8 caractères'),
  confirm_password: z.string(),
}).refine((data) => data.password === data.confirm_password, {
  message: 'Les mots de passe ne correspondent pas',
  path: ['confirm_password'],
})

export default function RegisterPage() {
  const navigate = useNavigate()
  const registerUser = useAuthStore((state) => state.register)
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data) => {
    try {
      setError('')
      await registerUser({
        full_name: data.full_name,
        email: data.email,
        password: data.password,
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'inscription')
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Brain className="w-12 h-12 text-primary-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Créer un compte</h1>
          <p className="text-dark-400">Rejoignez CVision AI dès maintenant</p>
        </div>

        <div className="glass-card p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <Input
              label="Nom complet"
              placeholder="Jean Dupont"
              {...register('full_name')}
              error={errors.full_name?.message}
            />

            <Input
              label="Email"
              type="email"
              placeholder="jean@email.com"
              {...register('email')}
              error={errors.email?.message}
            />

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

            <Input
              label="Confirmer le mot de passe"
              type="password"
              placeholder="••••••••"
              {...register('confirm_password')}
              error={errors.confirm_password?.message}
            />

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Création...' : (
                <>
                  <UserPlus className="w-5 h-5 mr-2" />
                  S'inscrire
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-dark-400 text-sm">
              Déjà un compte ?{' '}
              <Link to="/login" className="text-primary-400 hover:text-primary-300 transition-colors">
                Se connecter
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}