import React, { useState } from 'react'
import { itemsApi } from '../api/client'

export default function CorrectionModal({ item, isOpen, onClose, onSuccess }) {
  const [newLabel, setNewLabel] = useState(item?.final_label || '')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!newLabel.trim()) {
      setError('Label cannot be empty')
      return
    }

    if (newLabel.length > 50) {
      setError('Label must be 50 characters or less')
      return
    }

    setIsLoading(true)

    try {
      const result = await itemsApi.correctLabel(item.id, newLabel)
      onSuccess(result)
      onClose()
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen || !item) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Correct Label</h3>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Item Preview
              </label>
              <div className="p-3 bg-gray-50 rounded border border-gray-200 text-sm text-gray-600 max-h-24 overflow-y-auto">
                {item.content_preview.length > 200
                  ? `${item.content_preview.substring(0, 200)}...`
                  : item.content_preview}
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AI Label
              </label>
              <div className="p-3 bg-blue-50 rounded border border-blue-200 text-sm text-blue-900">
                <span className="font-semibold">{item.final_label}</span>
                {item.confidence_score && (
                  <span className="ml-2 text-xs text-blue-700">
                    (Confidence: {(item.confidence_score * 100).toFixed(0)}%)
                  </span>
                )}
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Corrected Label
              </label>
              <input
                type="text"
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                placeholder="Enter the correct label"
                maxLength="50"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isLoading}
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-1">
                {newLabel.length}/50 characters
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </div>

          <div className="px-6 py-4 border-t border-gray-200 flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Saving...' : 'Confirm'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
