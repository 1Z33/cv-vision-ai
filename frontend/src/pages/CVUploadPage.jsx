import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'

export default function CVUploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile && (selectedFile.type === 'application/pdf' || selectedFile.name.endsWith('.pdf'))) {
      setFile(selectedFile)
      setUploadStatus(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('/api/v1/cvs/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      })

      if (response.ok) {
        const data = await response.json()
        setUploadStatus('success')
        setTimeout(() => navigate(`/cv-analysis/${data.id}`), 1500)
      } else {
        setUploadStatus('error')
      }
    } catch (error) {
      console.error('Upload error:', error)
      setUploadStatus('error')
    } finally {
      setUploading(false)
    }
  }

  const removeFile = () => {
    setFile(null)
    setUploadStatus(null)
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 animate-fade-in">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Analyser votre CV</h1>
        <p className="text-dark-400">Uploadez votre CV en PDF pour obtenir une analyse détaillée</p>
      </div>

      <Card className="p-8">
        {!file ? (
          <div className="border-2 border-dashed border-dark-600 rounded-xl p-12 text-center hover:border-dark-500 hover:bg-dark-800/50 transition-all">
            <Upload className="w-12 h-12 text-primary-500 mx-auto mb-4" />
            <p className="text-lg font-medium text-white mb-2">Sélectionnez votre CV PDF</p>
            <p className="text-dark-400 text-sm mb-4">Cliquez ci-dessous pour choisir un fichier</p>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="block w-full text-sm text-dark-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary-600 file:text-white hover:file:bg-primary-500 cursor-pointer"
            />
            <p className="text-xs text-dark-500 mt-4">PDF uniquement • Max 5MB</p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center gap-4 p-4 bg-dark-800/50 rounded-lg border border-dark-700">
              <div className="w-12 h-12 bg-red-500/10 rounded-lg flex items-center justify-center">
                <FileText className="w-6 h-6 text-red-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-white truncate">{file.name}</p>
                <p className="text-sm text-dark-400">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
              {!uploading && (
                <button onClick={removeFile} className="p-2 text-dark-400 hover:text-red-400 transition-colors">
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {uploadStatus === 'success' && (
              <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-3 text-green-400">
                <CheckCircle className="w-5 h-5" />
                <span>CV analysé avec succès ! Redirection...</span>
              </div>
            )}

            {uploadStatus === 'error' && (
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400">
                <AlertCircle className="w-5 h-5" />
                <span>Erreur lors de l'upload. Veuillez réessayer.</span>
              </div>
            )}

            <Button onClick={handleUpload} disabled={uploading || uploadStatus === 'success'} className="w-full">
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Analyse en cours...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-2" />
                  Lancer l'analyse IA
                </>
              )}
            </Button>
          </div>
        )}
      </Card>
    </div>
  )
}