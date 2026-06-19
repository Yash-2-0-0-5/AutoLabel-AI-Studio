import React, { useState, useEffect } from 'react'
import { datasetsApi } from '../api/client'
import CorrectionModal from './CorrectionModal'

export default function ReviewQueue() {
  const [datasets, setDatasets] = useState([])
  const [reviewItems, setReviewItems] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedItem, setSelectedItem] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [totalItems, setTotalItems] = useState(0)

  useEffect(() => {
    loadReviewQueue()
    // Poll every 3 seconds
    const interval = setInterval(loadReviewQueue, 3000)
    return () => clearInterval(interval)
  }, [])

  const loadReviewQueue = async () => {
    try {
      setIsLoading(true)
      const datasetsResponse = await datasetsApi.list()
      setDatasets(datasetsResponse.datasets)

      // Load items from each dataset and filter for review
      const allReviewItems = []

      for (const dataset of datasetsResponse.datasets) {
        try {
          const itemsResponse = await datasetsApi.getItems(dataset.id)
          const filtered = itemsResponse.items.filter(
            (item) =>
              (item.confidence_score < 0.7 || !item.is_reviewed) &&
              item.final_label
          )
          allReviewItems.push(
            ...filtered.map((item) => ({
              ...item,
              dataset_name: dataset.name,
              dataset_id: dataset.id,
            }))
          )
        } catch (err) {
          // Skip datasets with errors
        }
      }

      setTotalItems(allReviewItems.length)
      // Sort by confidence score (lowest first)
      const sorted = allReviewItems.sort(
        (a, b) => (a.confidence_score || 0) - (b.confidence_score || 0)
      )
      setReviewItems(sorted)
    } catch (err) {
      console.error('Failed to load review queue:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleOpenModal = (item) => {
    setSelectedItem(item)
    setIsModalOpen(true)
  }

  const handleCorrectionSuccess = (result) => {
    // Remove item from review queue
    setReviewItems(reviewItems.filter((item) => item.id !== result.item_id))
    setTotalItems(totalItems - 1)
  }

  const getConfidenceColor = (score) => {
    if (score === 1.0) return 'bg-green-100 text-green-800'
    if (score >= 0.8) return 'bg-green-50 text-green-700'
    if (score >= 0.6) return 'bg-yellow-50 text-yellow-700'
    return 'bg-red-50 text-red-700'
  }

  const getPriorityLevel = (item) => {
    if (!item.is_reviewed) return 'HIGH'
    if (item.confidence_score < 0.5) return 'CRITICAL'
    if (item.confidence_score < 0.7) return 'HIGH'
    return 'MEDIUM'
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'CRITICAL':
        return 'text-red-700 bg-red-50'
      case 'HIGH':
        return 'text-orange-700 bg-orange-50'
      default:
        return 'text-yellow-700 bg-yellow-50'
    }
  }

  return (
    <div className="space-y-4">
      {/* Header Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <p className="text-sm text-red-700 font-semibold">Critical</p>
          <p className="text-3xl font-bold text-red-900">
            {reviewItems.filter(
              (item) => item.confidence_score < 0.5 && !item.is_reviewed
            ).length}
          </p>
          <p className="text-xs text-red-600 mt-1">Requires immediate review</p>
        </div>

        <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
          <p className="text-sm text-orange-700 font-semibold">High Priority</p>
          <p className="text-3xl font-bold text-orange-900">
            {reviewItems.filter((item) => !item.is_reviewed).length}
          </p>
          <p className="text-xs text-orange-600 mt-1">Not yet reviewed</p>
        </div>

        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <p className="text-sm text-blue-700 font-semibold">In Queue</p>
          <p className="text-3xl font-bold text-blue-900">{totalItems}</p>
          <p className="text-xs text-blue-600 mt-1">Items needing review</p>
        </div>
      </div>

      {/* Items List */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Review Queue</h2>
          <p className="text-sm text-gray-600 mt-1">
            {isLoading ? 'Updating...' : 'Click on any item to correct the label'}
          </p>
        </div>

        {isLoading && reviewItems.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Loading review queue...</p>
          </div>
        ) : reviewItems.length === 0 ? (
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
                d="M5 13l4 4L19 7"
              />
            </svg>
            <p className="text-gray-600 font-medium">All items reviewed!</p>
            <p className="text-sm text-gray-500 mt-1">
              No low-confidence or pending items to review
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Dataset
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
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {reviewItems.map((item) => {
                  const priority = getPriorityLevel(item)
                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleOpenModal(item)}
                    >
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 rounded text-xs font-bold ${getPriorityColor(
                            priority
                          )}`}
                        >
                          {priority}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {item.dataset_name}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                        {item.content_preview.length > 80
                          ? `${item.content_preview.substring(0, 80)}...`
                          : item.content_preview}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span className="px-3 py-1 bg-blue-50 text-blue-900 rounded-full text-xs font-semibold">
                          {item.final_label}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${getConfidenceColor(
                            item.confidence_score || 0
                          )}`}
                        >
                          {item.confidence_score
                            ? `${(item.confidence_score * 100).toFixed(0)}%`
                            : 'N/A'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleOpenModal(item)
                          }}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 font-medium"
                        >
                          Review
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
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
