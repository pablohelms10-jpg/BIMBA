'use client'

import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import type { Document } from '@/lib/types'

interface UseDocumentsReturn {
  documents: Document[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  deleteDocument: (id: string) => Promise<void>
}

export function useDocuments(): UseDocumentsReturn {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await api.documents.list()
      setDocuments(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error cargando documentos'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const deleteDocument = useCallback(async (id: string) => {
    try {
      await api.documents.delete(id)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error eliminando documento'
      setError(message)
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  return { documents, isLoading, error, refetch: fetchDocuments, deleteDocument }
}
