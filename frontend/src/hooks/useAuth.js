import { useEffect } from 'react'
import { useAuthStore } from '../store/authStore'

export function useAuth() {
  const { user, isAuthenticated, initializeAuth, logout } = useAuthStore()

  useEffect(() => {
    initializeAuth()
  }, [])

  return { user, isAuthenticated, logout }
}