import { useState, useEffect } from 'react'
import UploadSection from './components/UploadSection'
import DatasetsList from './components/DatasetsList'
import DatasetView from './components/DatasetView'
import ReviewQueue from './components/ReviewQueue'
import './App.css'

function App() {
  const [currentView, setCurrentView] = useState('dashboard')
  const [selectedDatasetId, setSelectedDatasetId] = useState(null)
  const [backendHealth, setBackendHealth] = useState(true)

  useEffect(() => {
    // Check backend health on load
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(() => setBackendHealth(true))
      .catch(() => setBackendHealth(false))
  }, [])

  const handleDatasetSelect = (datasetId) => {
    setSelectedDatasetId(datasetId)
    setCurrentView('dataset')
  }

  const handleBack = () => {
    setCurrentView('dashboard')
    setSelectedDatasetId(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-900">
              AutoLabel AI Studio
            </h1>
            {!backendHealth && (
              <div className="px-4 py-2 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700 font-medium">
                  Backend unavailable - Check if server is running
                </p>
              </div>
            )}
          </div>

          {/* Navigation Tabs */}
          <div className="flex gap-2 border-b border-gray-200">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                currentView === 'dashboard'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setCurrentView('review')}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                currentView === 'review'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Review Queue
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {currentView === 'dashboard' && !selectedDatasetId && (
          <div className="space-y-6">
            <UploadSection
              onUploadSuccess={() => {
                // Refresh dataset list by reloading
                window.location.reload()
              }}
            />
            <DatasetsList onSelectDataset={handleDatasetSelect} />
          </div>
        )}

        {currentView === 'dataset' && selectedDatasetId && (
          <DatasetView
            datasetId={selectedDatasetId}
            onBack={handleBack}
          />
        )}

        {currentView === 'review' && (
          <ReviewQueue />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-400 text-sm py-6 mt-12">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p>AutoLabel AI Studio v0.1.0 | Powered by Gemini AI</p>
        </div>
      </footer>
    </div>
  )
}

export default App
