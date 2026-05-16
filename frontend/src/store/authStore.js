import { create } from 'zustand'
import { authService } from '../services/authService'

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  initializeAuth: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isLoading: false, isAuthenticated: false })
      return
    }

    try {
      const user = await authService.getMe()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch (error) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },

  login: async (email, password) => {
    const data = await authService.login(email, password)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    
    const user = await authService.getMe()
    set({ user, isAuthenticated: true })
  },

  register: async (userData) => {
    await authService.register(userData)
    // Auto-login après inscription
    await get().login(userData.email, userData.password)
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  updateUser: (userData) => {
    set((state) => ({
      user: { ...state.user, ...userData }
    }))
  }
}))