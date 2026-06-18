import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/')
      .then(res => res.json())
      .then(data => {
        setMessage(data.message)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full">
          <h1 className="text-3xl font-bold text-gray-800 mb-4 text-center">
            AutoLabel AI Studio
          </h1>

          {loading ? (
            <p className="text-gray-600 text-center">Connecting to backend...</p>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded p-4">
              <p className="text-red-700">Error: {error}</p>
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded p-4">
              <p className="text-green-700 text-center font-semibold">{message}</p>
            </div>
          )}

          <div className="mt-6 text-center text-gray-600 text-sm">
            <p>Ready for intelligent data labeling</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
