import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Datasets API
export const datasetsApi = {
  list: async () => {
    const response = await client.get('/datasets')
    return response.data
  },

  get: async (datasetId) => {
    const response = await client.get(`/datasets/${datasetId}`)
    return response.data
  },

  getItems: async (datasetId) => {
    const response = await client.get(`/datasets/${datasetId}/items`)
    return response.data
  },

  getStatus: async (datasetId) => {
    const response = await client.get(`/datasets/${datasetId}/process/status`)
    return response.data
  },

  process: async (datasetId) => {
    const response = await client.post(`/datasets/${datasetId}/process`)
    return response.data
  },
}

// Upload API
export const uploadApi = {
  uploadFile: async (file, datasetName = null) => {
    const formData = new FormData()
    formData.append('file', file)
    if (datasetName) {
      formData.append('dataset_name', datasetName)
    }

    const response = await client.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

// Items API
export const itemsApi = {
  get: async (itemId) => {
    const response = await client.get(`/items/${itemId}`)
    return response.data
  },

  label: async (itemId) => {
    const response = await client.post(`/items/${itemId}/label`)
    return response.data
  },

  correctLabel: async (itemId, correctedLabel) => {
    const response = await client.put(`/items/${itemId}/correct`, {
      corrected_label: correctedLabel,
    })
    return response.data
  },

  review: async (itemId, isReviewed) => {
    const response = await client.put(`/items/${itemId}/review`, {
      is_reviewed: isReviewed,
    })
    return response.data
  },
}

export default client
