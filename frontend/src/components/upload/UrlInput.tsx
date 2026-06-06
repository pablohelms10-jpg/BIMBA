'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Link, Youtube, Globe, Loader2, ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function isYouTubeUrl(url: string): boolean {
  return /(?:youtu\.be|youtube\.com\/watch|youtube\.com\/shorts)/i.test(url)
}

function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export function UrlInput() {
  const router = useRouter()
  const [url, setUrl] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isYoutube = isYouTubeUrl(url)
  const isValid = url.trim().length > 0 && isValidUrl(url.trim())

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValid || isSubmitting) return
    setIsSubmitting(true)
    setError(null)
    try {
      const doc = await api.documents.submitUrl(url.trim())
      router.push(`/documents/${doc.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al procesar la URL')
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div
        className={cn(
          'flex items-center gap-3 rounded-xl border bg-[#111827] px-4 py-3 transition-colors',
          error ? 'border-red-700' : 'border-[#1f2937] focus-within:border-[#3b82f6]'
        )}
      >
        <div className="shrink-0">
          {isYoutube ? (
            <Youtube className="h-5 w-5 text-red-500" />
          ) : url.length > 0 ? (
            <Globe className="h-5 w-5 text-[#3b82f6]" />
          ) : (
            <Link className="h-5 w-5 text-[#9ca3af]" />
          )}
        </div>
        <input
          type="url"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value)
            setError(null)
          }}
          placeholder="https://youtube.com/watch?v=... o cualquier URL"
          className="flex-1 bg-transparent text-sm text-[#f9fafb] placeholder-[#9ca3af] outline-none"
        />
        <Button
          type="submit"
          size="sm"
          isLoading={isSubmitting}
          disabled={!isValid || isSubmitting}
          className="shrink-0"
        >
          {!isSubmitting && <ArrowRight className="h-4 w-4" />}
          Procesar
        </Button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {isYoutube && !error && (
        <p className="text-xs text-[#9ca3af]">
          Se extraerá el audio del video de YouTube automáticamente.
        </p>
      )}
    </form>
  )
}
