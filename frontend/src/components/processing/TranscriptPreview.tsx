'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import type { AudioSegment } from '@/lib/types'
import { formatTime } from '@/lib/utils'
import { Loader2, Mic } from 'lucide-react'

interface TranscriptPreviewProps {
  documentId: string
}

export function TranscriptPreview({ documentId }: TranscriptPreviewProps) {
  const [segments, setSegments] = useState<AudioSegment[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.jobs.getTranscript(documentId)
      .then(setSegments)
      .catch((err) => setError(err instanceof Error ? err.message : 'Error cargando transcripción'))
      .finally(() => setIsLoading(false))
  }, [documentId])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-[#3b82f6]" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-800 bg-red-950/20 p-4">
        <p className="text-sm text-red-400">{error}</p>
      </div>
    )
  }

  if (segments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-12 text-[#9ca3af]">
        <Mic className="h-10 w-10" />
        <p className="text-sm">No hay transcripción disponible todavía.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-2">
      {segments.map((seg) => (
        <div
          key={seg.id}
          className="flex gap-4 rounded-lg border border-[#1f2937] bg-[#111827] p-4"
        >
          <div className="shrink-0 text-right">
            <span className="inline-block rounded-md bg-blue-900/30 border border-blue-800/40 px-2 py-0.5 text-xs font-mono text-[#3b82f6]">
              {formatTime(seg.start_time)}
            </span>
          </div>
          <p className="flex-1 text-sm text-[#f9fafb] leading-relaxed">{seg.transcript}</p>
        </div>
      ))}
    </div>
  )
}
