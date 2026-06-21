import axios from 'axios'

const apiBase = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  // VITE_API_URL est typiquement .../_/backend/api
  // En dev, le proxy Vite s'occupe de /api
  baseURL: `${apiBase}/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})


// Intercepteur pour ajouter le token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Intercepteur pour gérer les erreurs 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Tentative de refresh token
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', response.data.access_token)
          localStorage.setItem('refresh_token', response.data.refresh_token)
          
          // Retry la requête originale
          error.config.headers.Authorization = `Bearer ${response.data.access_token}`
          return axios(error.config)
        } catch (refreshError) {
          // Refresh échoué, déconnexion
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api