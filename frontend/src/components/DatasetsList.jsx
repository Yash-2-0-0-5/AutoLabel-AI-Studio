import React, { useState, useEffect } from 'react'
import { datasetsApi } from '../api/client'

export default function DatasetsList({ onSelectDataset }) {
  const [datasets, setDatasets] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDatasets()
    // Poll every 5 seconds
    const interval = setInterval(loadDatasets, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadDatasets = async () => {
    try {
      setIsLoading(true)
      const response = await datasetsApi.list()
      setDatasets(response.datasets)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const getFileTypeIcon = (fileType) => {
    switch (fileType) {
      case 'csv':
        return '📄'
      case 'excel':
        return '📊'
      case 'json':
        return '{}'
      case 'image':
        return '🖼️'
      case 'audio':
        return '🎵'
      default:
        return '📁'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Datasets</h2>
        <button
          onClick={loadDatasets}
          disabled={isLoading}
          className="px-4 py-2 text-sm bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 disabled:opacity-50 font-medium"
        >
          {isLoading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="mx-6 my-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {isLoading && datasets.length === 0 ? (
        <div className="px-6 py-12 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading datasets...</p>
        </div>
      ) : datasets.length === 0 ? (
        <div className="px-6 py-12 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6v6m0 0v6m0-6h6m0 0h6m-6-6h6m0 0h6"
            />
          </svg>
          <p className="text-gray-600 font-medium">No datasets yet</p>
          <p className="text-sm text-gray-500 mt-1">Upload a file to create a dataset</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
          {datasets.map((dataset) => (
            <div
              key={dataset.id}
              onClick={() => onSelectDataset(dataset.id)}
              className="p-4 border border-gray-200 rounded-lg hover:shadow-md hover:border-blue-300 cursor-pointer transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-3xl">
                  {getFileTypeIcon(dataset.file_type)}
                </span>
                <span className="px-2 py-1 text-xs font-semibold bg-gray-100 text-gray-700 rounded">
                  {dataset.file_type.toUpperCase()}
                </span>
              </div>

              <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
                {dataset.name}
              </h3>

              {dataset.description && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                  {dataset.description}
                </p>
              )}

              <div className="text-xs text-gray-500 mb-4">
                Created: {new Date(dataset.created_at).toLocaleDateString()}
              </div>

              <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm">
                View Dataset
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
