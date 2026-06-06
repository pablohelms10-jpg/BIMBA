'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { CheckCircle, Circle, Loader2, XCircle } from 'lucide-react'
import { useJobStatus } from '@/hooks/useJobStatus'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

const STAGES = [
  { label: 'Extrayendo audio', threshold: 10 },
  { label: 'Transcribiendo', threshold: 30 },
  { label: 'Detectando diapositivas', threshold: 50 },
  { label: 'Ejecutando OCR', threshold: 65 },
  { label: 'Vinculación semántica', threshold: 80 },
  { label: 'Generando apuntes', threshold: 95 },
  { label: 'Completado', threshold: 100 },
]

interface JobProgressProps {
  documentId: string
}

export function JobProgress({ documentId }: JobProgressProps) {
  const { job, isLoading, error } = useJobStatus(documentId)
  const router = useRouter()

  useEffect(() => {
    if (job?.status === 'completed') {
      const timer = setTimeout(() => {
        router.push(`/documents/${documentId}/notes`)
      }, 1500)
      return () => clearTimeout(timer)
    }
  }, [job?.status, documentId, router])

  if (isLoading && !job) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-[#3b82f6]" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-800 bg-red-950/20 p-6">
        <div className="flex items-center gap-3">
          <XCircle className="h-6 w-6 text-red-400" />
          <div>
            <p className="font-medium text-red-300">Error en el procesamiento</p>
            <p className="mt-1 text-sm text-red-400">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!job) return null

  const progress = job.progress ?? 0
  const isFailed = job.status === 'failed'
  const isCompleted = job.status === 'completed'

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-[#1f2937] bg-[#111827] p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-semibold text-[#f9fafb]">
            {isCompleted ? 'Procesamiento completado' : isFailed ? 'Error en el procesamiento' : 'Procesando documento...'}
          </h3>
          <span className="text-sm font-medium text-[#3b82f6]">{progress}%</span>
        </div>
        <Progress
          value={progress}
          color={isCompleted ? 'green' : isFailed ? 'red' : 'blue'}
          className="mb-2"
        />
        {job.current_stage && !isCompleted && (
          <p className="text-sm text-[#9ca3af]">{job.current_stage}</p>
        )}
      </div>

      <div className="space-y-2">
        {STAGES.map((stage, idx) => {
          const reached = progress >= stage.threshold
          const isActive =
            !isCompleted &&
            !isFailed &&
            progress >= (STAGES[idx - 1]?.threshold ?? 0) &&
            progress < stage.threshold

          return (
            <div
              key={stage.label}
              className={cn(
                'flex items-center gap-3 rounded-lg px-4 py-3 transition-all',
                isActive ? 'bg-blue-950/30 border border-blue-800/40' : 'bg-[#111827]'
              )}
            >
              {isFailed && isActive ? (
                <XCircle className="h-5 w-5 shrink-0 text-red-400" />
              ) : reached || (isCompleted && idx === STAGES.length - 1) ? (
                <CheckCircle className="h-5 w-5 shrink-0 text-[#10b981]" />
              ) : isActive ? (
                <Loader2 className="h-5 w-5 shrink-0 animate-spin text-[#3b82f6]" />
              ) : (
                <Circle className="h-5 w-5 shrink-0 text-[#1f2937]" />
              )}
              <span
                className={cn(
                  'text-sm',
                  reached || isActive ? 'text-[#f9fafb]' : 'text-[#9ca3af]',
                  isActive && 'font-medium'
                )}
              >
                {stage.label}
                {idx === STAGES.length - 1 && isCompleted ? ' ✓' : ''}
              </span>
              <span className="ml-auto text-xs text-[#9ca3af]">{stage.threshold}%</span>
            </div>
          )
        })}
      </div>

      {isFailed && job.error_message && (
        <div className="rounded-lg border border-red-800 bg-red-950/20 p-4">
          <p className="text-sm text-red-400">{job.error_message}</p>
        </div>
      )}

      {isCompleted && (
        <div className="rounded-lg border border-emerald-800 bg-emerald-950/20 p-4 text-center">
          <p className="text-sm text-emerald-400 font-medium">
            Redirigiendo a los apuntes...
          </p>
        </div>
      )}
    </div>
  )
}
