'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { api } from '@/lib/api'
import type { VisualFrame } from '@/lib/types'
import { formatTime } from '@/lib/utils'
import { Loader2, Layers, Maximize2 } from 'lucide-react'
import { Dialog } from '@/components/ui/dialog'

interface FrameGalleryProps {
  documentId: string
}

export function FrameGallery({ documentId }: FrameGalleryProps) {
  const [frames, setFrames] = useState<VisualFrame[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFrame, setSelectedFrame] = useState<VisualFrame | null>(null)

  useEffect(() => {
    api.jobs.getFrames(documentId)
      .then(setFrames)
      .catch((err) => setError(err instanceof Error ? err.message : 'Error cargando diapositivas'))
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

  if (frames.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-12 text-[#9ca3af]">
        <Layers className="h-10 w-10" />
        <p className="text-sm">No se detectaron diapositivas todavía.</p>
      </div>
    )
  }

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {frames.map((frame) => (
          <button
            key={frame.id}
            onClick={() => setSelectedFrame(frame)}
            className="group relative overflow-hidden rounded-xl border border-[#1f2937] bg-[#111827] hover:border-[#3b82f6] transition-all text-left"
          >
            <div className="relative aspect-video bg-[#1f2937]">
              <Image
                src={frame.image_url}
                alt={frame.slide_title ?? `Diapositiva ${frame.slide_number}`}
                fill
                className="object-cover"
                sizes="(max-width: 768px) 50vw, 25vw"
              />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="rounded-md bg-black/60 p-1">
                  <Maximize2 className="h-3.5 w-3.5 text-white" />
                </div>
              </div>
            </div>
            <div className="p-3">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold text-[#3b82f6]">#{frame.slide_number}</span>
                <span className="text-xs text-[#9ca3af] font-mono">{formatTime(frame.timestamp)}</span>
              </div>
              {frame.slide_title && (
                <p className="mt-1 text-xs text-[#f9fafb] truncate">{frame.slide_title}</p>
              )}
            </div>
          </button>
        ))}
      </div>

      <Dialog open={!!selectedFrame} onClose={() => setSelectedFrame(null)} className="max-w-3xl">
        {selectedFrame && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-[#3b82f6]">Diapositiva {selectedFrame.slide_number}</span>
              {selectedFrame.slide_title && (
                <span className="text-sm text-[#f9fafb]">{selectedFrame.slide_title}</span>
              )}
              <span className="ml-auto text-sm font-mono text-[#9ca3af]">{formatTime(selectedFrame.timestamp)}</span>
            </div>
            <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-[#1f2937]">
              <Image
                src={selectedFrame.image_url}
                alt={selectedFrame.slide_title ?? `Diapositiva ${selectedFrame.slide_number}`}
                fill
                className="object-contain"
                sizes="80vw"
              />
            </div>
            {selectedFrame.ocr_text && (
              <div className="rounded-lg bg-[#1f2937] p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#9ca3af]">Texto detectado (OCR)</p>
                <p className="text-sm text-[#f9fafb] whitespace-pre-wrap">{selectedFrame.ocr_text}</p>
              </div>
            )}
          </div>
        )}
      </Dialog>
    </>
  )
}
