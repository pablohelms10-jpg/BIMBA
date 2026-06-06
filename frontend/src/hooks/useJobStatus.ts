'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '@/lib/api'
import type { ProcessingJob } from '@/lib/types'

interface UseJobStatusReturn {
  job: ProcessingJob | null
  isLoading: boolean
  error: string | null
  refetch: () => void
}

export function useJobStatus(documentId: string | null): UseJobStatusReturn {
  const [job, setJob] = useState<ProcessingJob | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const isMountedRef = useRef(true)

  const fetchStatus = useCallback(async () => {
    if (!documentId) return
    try {
      const data = await api.jobs.getStatus(documentId)
      if (!isMountedRef.current) return
      setJob(data)
      setError(null)

      // Stop polling when terminal state reached
      if (data.status === 'completed' || data.status === 'failed') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
      }
    } catch (err) {
      if (!isMountedRef.current) return
      const message = err instanceof Error ? err.message : 'Error fetching job status'
      setError(message)
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false)
      }
    }
  }, [documentId])

  useEffect(() => {
    isMountedRef.current = true
    if (!documentId) return

    setIsLoading(true)
    fetchStatus()

    intervalRef.current = setInterval(fetchStatus, 2000)

    return () => {
      isMountedRef.current = false
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [documentId, fetchStatus])

  return { job, isLoading, error, refetch: fetchStatus }
}
