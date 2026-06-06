import axios from 'axios'
import type { Document, ProcessingJob, AudioSegment, VisualFrame, Notes } from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

export const api = {
  documents: {
    upload: async (file: File, onProgress?: (pct: number) => void): Promise<Document> => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await client.post<Document>('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(pct)
          }
        },
      })
      return response.data
    },

    submitUrl: async (url: string): Promise<Document> => {
      const response = await client.post<Document>('/documents/url', { url })
      return response.data
    },

    list: async (): Promise<Document[]> => {
      const response = await client.get<Document[]>('/documents')
      return response.data
    },

    get: async (id: string): Promise<Document> => {
      const response = await client.get<Document>(`/documents/${id}`)
      return response.data
    },

    delete: async (id: string): Promise<void> => {
      await client.delete(`/documents/${id}`)
    },
  },

  jobs: {
    getStatus: async (documentId: string): Promise<ProcessingJob> => {
      const response = await client.get<ProcessingJob>(`/jobs/${documentId}`)
      return response.data
    },

    getTranscript: async (documentId: string): Promise<AudioSegment[]> => {
      const response = await client.get<AudioSegment[]>(`/jobs/${documentId}/transcript`)
      return response.data
    },

    getFrames: async (documentId: string): Promise<VisualFrame[]> => {
      const response = await client.get<VisualFrame[]>(`/jobs/${documentId}/frames`)
      return response.data
    },
  },

  notes: {
    get: async (documentId: string): Promise<Notes> => {
      const response = await client.get<Notes>(`/notes/${documentId}`)
      return response.data
    },

    export: async (documentId: string, format: 'pdf' | 'docx' | 'md' | 'txt'): Promise<Blob> => {
      const response = await client.get(`/notes/${documentId}/export`, {
        params: { format },
        responseType: 'blob',
      })
      return response.data
    },

    updateLinks: async (documentId: string, links: unknown[]): Promise<void> => {
      await client.patch(`/notes/${documentId}/links`, { links })
    },
  },
}
