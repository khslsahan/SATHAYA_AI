import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface QueryRequest {
  query: string
  session_id?: string
}

export interface QueryResponse {
  answer: string
  citations: Array<{ type: string; full_text: string }>
  session_id: string
  sources?: Array<any>
  routing?: {
    category: string
    reasoning: string
  }
}

export async function sendQuery(query: string, sessionId?: string): Promise<QueryResponse> {
  try {
    const response = await apiClient.post<QueryResponse>('/query', {
      query,
      session_id: sessionId,
    })
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to send query')
    }
    throw error
  }
}

export async function getQueryHistory(sessionId: string) {
  try {
    const response = await apiClient.get(`/query/${sessionId}`)
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to get query history')
    }
    throw error
  }
}

