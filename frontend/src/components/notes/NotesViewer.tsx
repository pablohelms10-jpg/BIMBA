'use client'

import { useState } from 'react'
import type { Notes } from '@/lib/types'
import { NoteSection } from './NoteSection'
import { ExportMenu } from './ExportMenu'
import { LinkCorrector } from './LinkCorrector'
import { Button } from '@/components/ui/button'
import { Link2 } from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface NotesViewerProps {
  notes: Notes
}

export function NotesViewer({ notes }: NotesViewerProps) {
  const [linkCorrectorOpen, setLinkCorrectorOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[#0a0f1e]">
      {/* Sticky header */}
      <div className="sticky top-0 z-30 border-b border-[#1f2937] bg-[#0a0f1e]/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="min-w-0">
            <h1 className="truncate text-lg font-bold text-[#f9fafb]">{notes.document_title}</h1>
            <p className="text-xs text-[#9ca3af]">
              {notes.sections.length} secciones · Generado {formatDate(notes.generated_at)}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setLinkCorrectorOpen(true)}
            >
              <Link2 className="h-4 w-4" />
              <span className="hidden sm:inline">Corregir enlaces</span>
            </Button>
            <ExportMenu documentId={notes.document_id} documentTitle={notes.document_title} />
          </div>
        </div>
      </div>

      {/* Notes content */}
      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
        {notes.sections.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-20 text-[#9ca3af]">
            <p className="text-sm">No se encontraron secciones en los apuntes.</p>
          </div>
        ) : (
          <div className="space-y-10">
            {notes.sections.map((section, index) => (
              <NoteSection
                key={section.slide_number}
                section={section}
                index={index}
              />
            ))}
          </div>
        )}
      </main>

      <LinkCorrector
        documentId={notes.document_id}
        open={linkCorrectorOpen}
        onClose={() => setLinkCorrectorOpen(false)}
      />
    </div>
  )
}
