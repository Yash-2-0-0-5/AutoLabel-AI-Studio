import React, { useState } from 'react'
import { uploadApi } from '../api/client'

export default function UploadSection({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [datasetName, setDatasetName] = useState('')

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleFileChange = (e) => {
    const files = e.target.files
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleFileUpload = async (file) => {
    setIsLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await uploadApi.uploadFile(file, datasetName || undefined)

      setSuccess({
        datasetName: result.dataset_name,
        itemCount: result.item_count,
        strategy: result.recommended_strategy,
      })

      setDatasetName('')

      // Call parent callback with new dataset info
      if (onUploadSuccess) {
        onUploadSuccess(result)
      }

      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(null), 5000)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload Dataset</h2>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Dataset Name (Optional)
        </label>
        <input
          type="text"
          value={datasetName}
          onChange={(e) => setDatasetName(e.target.value)}
          placeholder="e.g., product_reviews_batch_1"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        />
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
        }`}
      >
        <div className="mb-4">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20a4 4 0 004 4h24a4 4 0 004-4V20"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M16 22l8-8 8 8M24 14v14"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        <p className="text-lg font-semibold text-gray-700 mb-2">
          Drag and drop your file here
        </p>
        <p className="text-sm text-gray-500 mb-4">
          Supports: CSV, Excel, JSON, Images, Audio
        </p>

        <label className="inline-block">
          <span className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition cursor-pointer">
            {isLoading ? 'Uploading...' : 'Browse Files'}
          </span>
          <input
            type="file"
            onChange={handleFileChange}
            className="hidden"
            disabled={isLoading}
            accept=".csv,.xlsx,.xls,.json,.jpg,.jpeg,.png,.gif,.bmp,.mp3,.wav,.flac,.m4a"
          />
        </label>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700 font-medium">Upload Failed</p>
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {success && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-700 font-medium">Upload Successful!</p>
          <p className="text-sm text-green-600">
            Dataset: <strong>{success.datasetName}</strong>
          </p>
          <p className="text-sm text-green-600">
            Items: <strong>{success.itemCount}</strong>
          </p>
          <p className="text-sm text-green-600">
            Strategy: <strong>{success.strategy}</strong>
          </p>
        </div>
      )}
    </div>
  )
}
