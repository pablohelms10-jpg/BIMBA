import Image from 'next/image'
import { formatTime } from '@/lib/utils'
import type { NoteSection as NoteSectionType } from '@/lib/types'
import { Clock } from 'lucide-react'

interface NoteSectionProps {
  section: NoteSectionType
  index: number
}

export function NoteSection({ section, index }: NoteSectionProps) {
  return (
    <article className="space-y-4">
      <div className="flex flex-wrap items-start gap-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl" role="img" aria-label="pin">📌</span>
          <h2 className="text-xl font-bold text-[#f9fafb]">
            Diapositiva {section.slide_number}
            {section.slide_title ? ` – ${section.slide_title}` : ''}
          </h2>
        </div>
        <div className="flex items-center gap-1.5 rounded-full border border-[#1f2937] bg-[#1f2937] px-3 py-1">
          <Clock className="h-3.5 w-3.5 text-[#3b82f6]" />
          <span className="text-xs font-mono text-[#9ca3af]">
            Minuto {formatTime(section.timestamp_start)}
          </span>
        </div>
      </div>

      {section.image_url && (
        <div className="relative aspect-video max-w-2xl overflow-hidden rounded-xl border border-[#1f2937] bg-[#111827]">
          <Image
            src={section.image_url}
            alt={`Diapositiva ${section.slide_number}`}
            fill
            className="object-contain"
            sizes="(max-width: 768px) 100vw, 672px"
          />
        </div>
      )}

      <div className="space-y-2">
        {section.content.map((line, i) => (
          <div key={i} className="flex items-start gap-3">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#3b82f6]" />
            <p className="text-[#f9fafb] leading-relaxed">{line}</p>
          </div>
        ))}
      </div>

      {index >= 0 && (
        <div className="border-t border-[#1f2937] pt-2" />
      )}
    </article>
  )
}
