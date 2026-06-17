import api from './api'

export const gapBridgeService = {
  async generatePlan(cvId) {
    const response = await api.post('/gap-bridge/generate', { cv_id: cvId })
    return response.data
  },

  async getPlan(planId) {
    const response = await api.get(`/gap-bridge/${planId}`)
    return response.data
  },

  async updateProgress({ itemId, status, progressPercent }) {
    const response = await api.post('/gap-bridge/progress', {
      item_id: itemId,
      status,
      progress_percent: progressPercent,
    })
    return response.data
  },

  async getSummary(planId) {
    const response = await api.get(`/gap-bridge/${planId}/summary`)
    return response.data
  },
}

