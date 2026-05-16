import { create } from 'zustand'

export const useCVStore = create((set) => ({
  cvs: [],
  currentAnalysis: null,
  loading: false,

  setCVs: (cvs) => set({ cvs }),
  addCV: (cv) => set((state) => ({ cvs: [cv, ...state.cvs] })),
  setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
  setLoading: (loading) => set({ loading }),
}))