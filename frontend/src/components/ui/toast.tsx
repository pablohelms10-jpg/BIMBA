'use client'

import * as React from 'react'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ToastVariant = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  message: string
  variant: ToastVariant
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (message: string, variant?: ToastVariant) => void
  removeToast: (id: string) => void
}

const ToastContext = React.createContext<ToastContextValue>({
  toasts: [],
  addToast: () => {},
  removeToast: () => {},
})

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([])

  const addToast = React.useCallback((message: string, variant: ToastVariant = 'info') => {
    const id = crypto.randomUUID()
    setToasts((prev) => [...prev, { id, message, variant }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  return React.useContext(ToastContext)
}

const variantConfig: Record<ToastVariant, { icon: React.ReactNode; style: string }> = {
  success: {
    icon: <CheckCircle className="h-5 w-5 text-emerald-400 shrink-0" />,
    style: 'border-emerald-800 bg-emerald-900/40',
  },
  error: {
    icon: <AlertCircle className="h-5 w-5 text-red-400 shrink-0" />,
    style: 'border-red-800 bg-red-900/40',
  },
  info: {
    icon: <Info className="h-5 w-5 text-blue-400 shrink-0" />,
    style: 'border-blue-800 bg-blue-900/40',
  },
}

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: string) => void }) {
  if (toasts.length === 0) return null
  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full">
      {toasts.map((toast) => {
        const config = variantConfig[toast.variant]
        return (
          <div
            key={toast.id}
            className={cn(
              'flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg text-[#f9fafb] text-sm',
              config.style
            )}
          >
            {config.icon}
            <span className="flex-1">{toast.message}</span>
            <button onClick={() => onRemove(toast.id)} className="text-[#9ca3af] hover:text-[#f9fafb]">
              <X className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
