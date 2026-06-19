import React, { useState, useEffect } from 'react'
import { datasetsApi } from '../api/client'
import CorrectionModal from './CorrectionModal'

export default function DatasetView({ datasetId, onBack }) {
  const [dataset, setDataset] = useState(null)
  const [items, setItems] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedItem, setSelectedItem] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [processingStatus, setProcessingStatus] = useState(null)

  useEffect(() => {
    loadDataset()
    // Poll status every 2 seconds
    const interval = setInterval(loadProcessingStatus, 2000)
    return () => clearInterval(interval)
  }, [datasetId])

  const loadDataset = async () => {
    try {
      setIsLoading(true)
      const response = await datasetsApi.get(datasetId)
      setDataset(response)

      const itemsResponse = await datasetsApi.getItems(datasetId)
      setItems(itemsResponse.items)

      loadProcessingStatus()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const loadProcessingStatus = async () => {
    try {
      const status = await datasetsApi.getStatus(datasetId)
      setProcessingStatus(status)
    } catch (err) {
      // Silently fail for polling
    }
  }

  const handleStartProcessing = async () => {
    try {
      setIsLoading(true)
      await datasetsApi.process(datasetId)
      loadProcessingStatus()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleOpenModal = (item) => {
    setSelectedItem(item)
    setIsModalOpen(true)
  }

  const handleCorrectionSuccess = (result) => {
    // Update the item in the list
    setItems(
      items.map((item) =>
        item.id === result.item_id ? { ...item, ...result } : item
      )
    )
    loadProcessingStatus()
  }

  const getConfidenceColor = (score) => {
    if (score === 1.0) return 'bg-green-100 text-green-800'
    if (score >= 0.8) return 'bg-green-50 text-green-700'
    if (score >= 0.6) return 'bg-yellow-50 text-yellow-700'
    return 'bg-red-50 text-red-700'
  }

  const getConfidenceIcon = (score) => {
    if (score === 1.0) return '✓'
    if (score >= 0.8) return '→'
    return '⚠'
  }

  if (isLoading && !items.length) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="text-gray-600 hover:text-gray-900 text-xl"
          >
            ←
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {dataset?.name}
            </h2>
            <p className="text-sm text-gray-600">
              Type: <span className="font-semibold">{dataset?.file_type}</span>
            </p>
          </div>
        </div>

        {processingStatus && (
          <div className="text-right">
            <div className="text-sm text-gray-600 mb-1">
              Progress: {processingStatus.completion_percentage}%
            </div>
            <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-300"
                style={{
                  width: `${processingStatus.completion_percentage}%`,
                }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {processingStatus.labeled_items}/{processingStatus.total_items}
              labeled
            </p>
          </div>
        )}
      </div>

      {/* Action Bar */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200 flex gap-2">
        <button
          onClick={handleStartProcessing}
          disabled={isLoading || !processingStatus?.unlabeled_items}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
        >
          {isLoading ? 'Processing...' : 'Start AI Labeling'}
        </button>
        <button
          onClick={loadDataset}
          disabled={isLoading}
          className="px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 disabled:opacity-50 text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mx-6 my-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Items Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                Preview
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                AI Label
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                Confidence
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {items.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                  No items in this dataset
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr
                  key={item.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleOpenModal(item)}
                >
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {item.id}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                    {item.content_preview.length > 100
                      ? `${item.content_preview.substring(0, 100)}...`
                      : item.content_preview}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className="px-3 py-1 bg-blue-50 text-blue-900 rounded-full text-xs font-semibold">
                      {item.final_label || '—'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1 ${getConfidenceColor(
                          item.confidence_score || 0
                        )}`}
                      >
                        {getConfidenceIcon(item.confidence_score || 0)}
                        {item.confidence_score
                          ? `${(item.confidence_score * 100).toFixed(0)}%`
                          : 'N/A'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    {item.is_reviewed ? (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                        Reviewed
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-semibold">
                        Pending
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleOpenModal(item)
                      }}
                      className="px-3 py-1 text-sm bg-gray-200 text-gray-900 rounded hover:bg-gray-300 font-medium"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      <CorrectionModal
        item={selectedItem}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false)
          setSelectedItem(null)
        }}
        onSuccess={handleCorrectionSuccess}
      />
    </div>
  )
}
