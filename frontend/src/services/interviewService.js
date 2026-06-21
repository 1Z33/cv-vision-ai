import api from './api'

export const interviewService = {
  async start(data) {
    const response = await api.post('/interviews/start', data)
    return response.data
  },


  async submitAnswer(sessionId, answer) {
    const response = await api.post(`/interviews/${sessionId}/answer`, { answer })
    return response.data
  },

  async getFeedback(sessionId) {
    const response = await api.get(`/interviews/${sessionId}/feedback`)
    return response.data
  },

  async getHistory() {
    const response = await api.get('/interviews/history')
    return response.data
  }
}