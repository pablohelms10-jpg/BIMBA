'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { NotesViewer } from '@/components/notes/NotesViewer'
import { api } from '@/lib/api'
import type { Notes } from '@/lib/types'
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react'

export default function NotesPage() {
  const params = useParams()
  const id = params.id as string
  const [notes, setNotes] = useState<Notes | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.notes.get(id)
      .then(setNotes)
      .catch((err) => setError(err instanceof Error ? err.message : 'Error cargando apuntes'))
      .finally(() => setIsLoading(false))
  }, [id])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0f1e]">
        <Loader2 className="h-8 w-8 animate-spin text-[#3b82f6]" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#0a0f1e] px-4">
        <div className="flex items-center gap-3 rounded-xl border border-red-800 bg-red-950/20 px-6 py-4">
          <AlertCircle className="h-6 w-6 text-red-400 shrink-0" />
          <div>
            <p className="font-medium text-red-300">No se pudieron cargar los apuntes</p>
            <p className="text-sm text-red-400 mt-1">{error}</p>
          </div>
        </div>
        <Link
          href={`/documents/${id}`}
          className="flex items-center gap-2 text-sm text-[#9ca3af] hover:text-[#f9fafb] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver al estado del documento
        </Link>
      </div>
    )
  }

  if (!notes) return null

  return <NotesViewer notes={notes} />
}
