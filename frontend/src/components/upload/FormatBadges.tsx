import { Film, Music, FileText, Image, Globe } from 'lucide-react'

const formats = [
  {
    icon: Film,
    label: 'Video',
    items: 'MP4, AVI, MKV, MOV',
    color: 'text-purple-400',
    bg: 'bg-purple-900/20 border-purple-800/40',
  },
  {
    icon: Music,
    label: 'Audio',
    items: 'MP3, WAV, M4A',
    color: 'text-pink-400',
    bg: 'bg-pink-900/20 border-pink-800/40',
  },
  {
    icon: FileText,
    label: 'Documentos',
    items: 'PDF, DOCX, TXT',
    color: 'text-amber-400',
    bg: 'bg-amber-900/20 border-amber-800/40',
  },
  {
    icon: Image,
    label: 'Imágenes',
    items: 'JPG, PNG',
    color: 'text-emerald-400',
    bg: 'bg-emerald-900/20 border-emerald-800/40',
  },
  {
    icon: Globe,
    label: 'Web',
    items: 'URLs, YouTube',
    color: 'text-blue-400',
    bg: 'bg-blue-900/20 border-blue-800/40',
  },
]

export function FormatBadges() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
      {formats.map(({ icon: Icon, label, items, color, bg }) => (
        <div
          key={label}
          className={`flex flex-col items-center gap-2 rounded-xl border p-3 ${bg}`}
        >
          <Icon className={`h-6 w-6 ${color}`} />
          <div className="text-center">
            <p className="text-xs font-semibold text-[#f9fafb]">{label}</p>
            <p className="text-[10px] text-[#9ca3af] mt-0.5">{items}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
