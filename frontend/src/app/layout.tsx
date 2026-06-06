import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'BIMBA - Plataforma de Apuntes Médicos con IA',
  description: 'Transforma tus clases en apuntes de estudio estructurados con inteligencia artificial',
  keywords: ['medicina', 'apuntes', 'IA', 'transcripción', 'diapositivas'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" className={inter.variable}>
      <body className={`${inter.className} bg-[#0a0f1e] text-[#f9fafb] min-h-screen`}>
        {children}
      </body>
    </html>
  )
}
