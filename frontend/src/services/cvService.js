import api from './api'

export const cvService = {
  async upload(file) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/cvs/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  async getAll() {
    const response = await api.get('/cvs')
    return response.data
  },

  async getOne(cvId) {
    const response = await api.get(`/cvs/${cvId}`)
    return response.data
  },

  async getAnalysis(cvId) {
    const response = await api.get(`/cvs/${cvId}/analysis`)
    return response.data
  },

  async delete(cvId) {
    await api.delete(`/cvs/${cvId}`)
  }
}