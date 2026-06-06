import Link from 'next/link'
import { Stethoscope } from 'lucide-react'

export function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-[#1f2937] bg-[#0a0f1e]/90 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#3b82f6] group-hover:bg-blue-500 transition-colors">
            <Stethoscope className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl font-bold text-[#f9fafb]">BIMBA</span>
        </Link>
        <nav className="flex items-center gap-1">
          <Link
            href="/"
            className="rounded-lg px-3 py-2 text-sm text-[#9ca3af] hover:text-[#f9fafb] hover:bg-[#1f2937] transition-colors"
          >
            Inicio
          </Link>
        </nav>
      </div>
    </header>
  )
}
