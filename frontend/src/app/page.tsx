import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { UploadZone } from '@/components/upload/UploadZone'
import { UrlInput } from '@/components/upload/UrlInput'
import { FormatBadges } from '@/components/upload/FormatBadges'
import { Stethoscope, Sparkles } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#0a0f1e]">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - hidden on mobile */}
        <div className="hidden lg:flex lg:h-[calc(100vh-4rem)] lg:sticky lg:top-16 overflow-hidden">
          <Sidebar />
        </div>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
            {/* Hero */}
            <div className="mb-10 text-center">
              <div className="mb-4 flex items-center justify-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#3b82f6] to-blue-700 shadow-lg shadow-blue-900/40">
                  <Stethoscope className="h-7 w-7 text-white" />
                </div>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-[#3b82f6]" />
                  <span className="text-sm font-medium text-[#3b82f6]">Impulsado por IA</span>
                </div>
              </div>
              <h1 className="text-4xl font-extrabold tracking-tight text-[#f9fafb] sm:text-5xl">
                BIMBA
              </h1>
              <p className="mt-3 text-xl font-medium text-[#9ca3af]">
                Plataforma de Apuntes Médicos con IA
              </p>
              <p className="mt-2 text-base text-[#9ca3af]">
                Transforma tus clases en apuntes de estudio estructurados
              </p>
            </div>

            {/* Upload section */}
            <div className="rounded-2xl border border-[#1f2937] bg-[#111827] p-6 shadow-xl">
              <div className="space-y-6">
                <div>
                  <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-[#9ca3af]">
                    Subir archivo
                  </h2>
                  <UploadZone />
                </div>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-[#1f2937]" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-[#111827] px-4 text-xs text-[#9ca3af]">o</span>
                  </div>
                </div>

                <div>
                  <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-[#9ca3af]">
                    URL o YouTube
                  </h2>
                  <UrlInput />
                </div>
              </div>
            </div>

            {/* Supported formats */}
            <div className="mt-8">
              <h3 className="mb-4 text-sm font-semibold text-[#9ca3af]">Formatos soportados</h3>
              <FormatBadges />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
