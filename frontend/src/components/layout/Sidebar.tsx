'use client'

import Link from 'next/link'
import { useDocuments } from '@/hooks/useDocuments'
import { Badge } from '@/components/ui/badge'
import { getSourceTypeLabel, formatDate } from '@/lib/utils'
import { FileText, Loader2, Trash2, RefreshCw } from 'lucide-react'

const statusVariantMap: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
  completed: 'success',
  processing: 'info',
  pending: 'warning',
  failed: 'error',
}

const statusLabelMap: Record<string, string> = {
  completed: 'Listo',
  processing: 'Procesando',
  pending: 'Pendiente',
  failed: 'Error',
}

export function Sidebar() {
  const { documents, isLoading, error, refetch, deleteDocument } = useDocuments()

  return (
    <aside className="w-72 shrink-0 border-r border-[#1f2937] bg-[#0a0f1e] flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-4 border-b border-[#1f2937]">
        <h2 className="text-sm font-semibold text-[#f9fafb]">Documentos recientes</h2>
        <button
          onClick={() => refetch()}
          className="text-[#9ca3af] hover:text-[#f9fafb] p-1 rounded hover:bg-[#1f2937] transition-colors"
          title="Actualizar"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-[#9ca3af]" />
          </div>
        )}
        {error && (
          <p className="px-4 py-4 text-xs text-red-400">{error}</p>
        )}
        {!isLoading && documents.length === 0 && !error && (
          <p className="px-4 py-6 text-xs text-[#9ca3af] text-center">
            Sin documentos aún. <br />Sube tu primer archivo arriba.
          </p>
        )}
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="group flex items-start gap-3 px-4 py-3 hover:bg-[#111827] transition-colors"
          >
            <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#1f2937]">
              <FileText className="h-4 w-4 text-[#3b82f6]" />
            </div>
            <div className="min-w-0 flex-1">
              <Link
                href={
                  doc.status === 'completed'
                    ? `/documents/${doc.id}/notes`
                    : `/documents/${doc.id}`
                }
                className="block truncate text-sm font-medium text-[#f9fafb] hover:text-[#3b82f6] transition-colors"
                title={doc.title}
              >
                {doc.title}
              </Link>
              <div className="mt-1 flex items-center gap-2">
                <Badge variant={statusVariantMap[doc.status] ?? 'default'} className="text-[10px] px-1.5 py-0">
                  {statusLabelMap[doc.status] ?? doc.status}
                </Badge>
                <span className="text-[10px] text-[#9ca3af]">{getSourceTypeLabel(doc.source_type)}</span>
              </div>
              <p className="mt-0.5 text-[10px] text-[#9ca3af]">{formatDate(doc.created_at)}</p>
            </div>
            <button
              onClick={() => deleteDocument(doc.id)}
              className="opacity-0 group-hover:opacity-100 p-1 rounded text-[#9ca3af] hover:text-red-400 hover:bg-red-900/20 transition-all"
              title="Eliminar"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </aside>
  )
}
