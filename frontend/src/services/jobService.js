import api from './api'

export const jobService = {
  async getAll() {
    const response = await api.get('/jobs')
    return response.data
  },

  async getOne(jobId) {
    const response = await api.get(`/jobs/${jobId}`)
    return response.data
  },

  async create(jobData) {
    const response = await api.post('/jobs', jobData)
    return response.data
  },

  async match(cvId, jobId) {
    const response = await api.post('/matches', { cv_id: cvId, job_id: jobId })
    return response.data
  },

  async getMatches(cvId) {
    const response = await api.get(`/matches/${cvId}`)
    return response.data
  }
}