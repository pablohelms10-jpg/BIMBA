'use client'

import { useState } from 'react'
import { Download, FileText, FileDown, Hash, AlignLeft, ChevronDown } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type ExportFormat = 'pdf' | 'docx' | 'md' | 'txt'

const FORMATS: { format: ExportFormat; label: string; icon: React.ComponentType<{ className?: string }>; ext: string }[] = [
  { format: 'pdf', label: 'PDF', icon: FileDown, ext: 'pdf' },
  { format: 'docx', label: 'Word (DOCX)', icon: FileText, ext: 'docx' },
  { format: 'md', label: 'Markdown', icon: Hash, ext: 'md' },
  { format: 'txt', label: 'Texto plano', icon: AlignLeft, ext: 'txt' },
]

interface ExportMenuProps {
  documentId: string
  documentTitle: string
}

export function ExportMenu({ documentId, documentTitle }: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [loadingFormat, setLoadingFormat] = useState<ExportFormat | null>(null)

  const handleExport = async (format: ExportFormat, ext: string) => {
    setLoadingFormat(format)
    setIsOpen(false)
    try {
      const blob = await api.notes.export(documentId, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${documentTitle.replace(/[^a-zA-Z0-9\s-]/g, '').trim()}.${ext}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export error:', err)
    } finally {
      setLoadingFormat(null)
    }
  }

  return (
    <div className="relative">
      <Button
        onClick={() => setIsOpen((v) => !v)}
        variant="outline"
        size="md"
        isLoading={loadingFormat !== null}
        className="gap-2"
      >
        <Download className="h-4 w-4" />
        Exportar
        <ChevronDown className={cn('h-4 w-4 transition-transform', isOpen && 'rotate-180')} />
      </Button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 top-full z-20 mt-2 w-48 rounded-xl border border-[#1f2937] bg-[#111827] shadow-2xl overflow-hidden">
            {FORMATS.map(({ format, label, icon: Icon, ext }) => (
              <button
                key={format}
                onClick={() => handleExport(format, ext)}
                className="flex w-full items-center gap-3 px-4 py-3 text-sm text-[#f9fafb] hover:bg-[#1f2937] transition-colors"
              >
                <Icon className="h-4 w-4 text-[#9ca3af]" />
                {label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
