'use client'

import { useState } from 'react'
import { Link2, Save, Plus, Trash2, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Dialog, DialogTitle } from '@/components/ui/dialog'

interface LinkEntry {
  id: string
  original: string
  corrected: string
}

interface LinkCorrectorProps {
  documentId: string
  open: boolean
  onClose: () => void
}

export function LinkCorrector({ documentId, open, onClose }: LinkCorrectorProps) {
  const [links, setLinks] = useState<LinkEntry[]>([
    { id: crypto.randomUUID(), original: '', corrected: '' },
  ])
  const [isSaving, setIsSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const addLink = () => {
    setLinks((prev) => [...prev, { id: crypto.randomUUID(), original: '', corrected: '' }])
  }

  const removeLink = (id: string) => {
    setLinks((prev) => prev.filter((l) => l.id !== id))
  }

  const updateLink = (id: string, field: 'original' | 'corrected', value: string) => {
    setLinks((prev) => prev.map((l) => (l.id === id ? { ...l, [field]: value } : l)))
  }

  const handleSave = async () => {
    const validLinks = links.filter((l) => l.original.trim() && l.corrected.trim())
    if (validLinks.length === 0) return
    setIsSaving(true)
    try {
      await api.notes.updateLinks(documentId, validLinks)
      setSaved(true)
      setTimeout(() => {
        setSaved(false)
        onClose()
      }, 1500)
    } catch (err) {
      console.error('Error saving links:', err)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogTitle>
        <div className="flex items-center gap-2">
          <Link2 className="h-5 w-5 text-[#3b82f6]" />
          Corrección de enlaces
        </div>
      </DialogTitle>
      <p className="mb-4 text-sm text-[#9ca3af]">
        Corrige los enlaces o referencias que no fueron detectados correctamente.
      </p>

      <div className="space-y-3 max-h-[40vh] overflow-y-auto pr-1">
        {links.map((link) => (
          <div key={link.id} className="flex items-start gap-2">
            <div className="flex-1 grid grid-cols-2 gap-2">
              <input
                value={link.original}
                onChange={(e) => updateLink(link.id, 'original', e.target.value)}
                placeholder="Texto original"
                className="rounded-lg border border-[#1f2937] bg-[#0a0f1e] px-3 py-2 text-sm text-[#f9fafb] placeholder-[#9ca3af] outline-none focus:border-[#3b82f6]"
              />
              <input
                value={link.corrected}
                onChange={(e) => updateLink(link.id, 'corrected', e.target.value)}
                placeholder="Corrección"
                className="rounded-lg border border-[#1f2937] bg-[#0a0f1e] px-3 py-2 text-sm text-[#f9fafb] placeholder-[#9ca3af] outline-none focus:border-[#3b82f6]"
              />
            </div>
            <button
              onClick={() => removeLink(link.id)}
              className="mt-2 p-1.5 text-[#9ca3af] hover:text-red-400 hover:bg-red-900/20 rounded transition-colors"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <Button onClick={addLink} variant="ghost" size="sm">
          <Plus className="h-4 w-4" />
          Añadir entrada
        </Button>
        <div className="flex gap-2">
          <Button onClick={onClose} variant="outline" size="sm">
            Cancelar
          </Button>
          <Button onClick={handleSave} isLoading={isSaving} size="sm">
            {saved ? (
              '¡Guardado!'
            ) : isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Save className="h-4 w-4" />
                Guardar
              </>
            )}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}
