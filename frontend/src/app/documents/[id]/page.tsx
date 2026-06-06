'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { Header } from '@/components/layout/Header'
import { JobProgress } from '@/components/processing/JobProgress'
import { TranscriptPreview } from '@/components/processing/TranscriptPreview'
import { FrameGallery } from '@/components/processing/FrameGallery'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { api } from '@/lib/api'
import type { Document } from '@/lib/types'
import { ArrowLeft, Loader2 } from 'lucide-react'

export default function DocumentPage() {
  const params = useParams()
  const id = params.id as string
  const [document, setDocument] = useState<Document | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    api.documents.get(id)
      .then(setDocument)
      .catch(console.error)
      .finally(() => setIsLoading(false))
  }, [id])

  return (
    <div className="flex min-h-screen flex-col bg-[#0a0f1e]">
      <Header />
      <main className="flex-1">
        <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
          {/* Back */}
          <Link
            href="/"
            className="mb-6 inline-flex items-center gap-2 text-sm text-[#9ca3af] hover:text-[#f9fafb] transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver al inicio
          </Link>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-[#3b82f6]" />
            </div>
          ) : (
            <>
              {/* Document header */}
              <div className="mb-8">
                <h1 className="text-2xl font-bold text-[#f9fafb]">
                  {document?.title ?? 'Documento'}
                </h1>
                <p className="mt-1 text-sm text-[#9ca3af]">
                  Procesando documento con inteligencia artificial...
                </p>
              </div>

              <Tabs defaultValue="status">
                <TabsList className="mb-6">
                  <TabsTrigger value="status">Estado</TabsTrigger>
                  <TabsTrigger value="transcript">Transcripción</TabsTrigger>
                  <TabsTrigger value="slides">Diapositivas</TabsTrigger>
                </TabsList>

                <TabsContent value="status">
                  <JobProgress documentId={id} />
                </TabsContent>

                <TabsContent value="transcript">
                  <TranscriptPreview documentId={id} />
                </TabsContent>

                <TabsContent value="slides">
                  <FrameGallery documentId={id} />
                </TabsContent>
              </Tabs>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
