import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from './store/authStore'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'

// Pages
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import CVUploadPage from './pages/CVUploadPage'
import CVAnalysisPage from './pages/CVAnalysisPage'
import InterviewPage from './pages/InterviewPage'
import InterviewFeedbackPage from './pages/InterviewFeedbackPage'
import JobsPage from './pages/JobsPage'
import MatchResultPage from './pages/MatchResultPage'

function App() {
  const initializeAuth = useAuthStore((state) => state.initializeAuth)

  useEffect(() => {
    initializeAuth()
  }, [])

  return (
    <div className="min-h-screen bg-dark-950 text-white flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/upload-cv" element={<CVUploadPage />} />
          <Route path="/cv-analysis/:cvId" element={<CVAnalysisPage />} />
          <Route path="/interview" element={<InterviewPage />} />
          <Route path="/interview-feedback/:sessionId" element={<InterviewFeedbackPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/match/:cvId" element={<MatchResultPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}

export default App