import * as React from 'react'
import { cn } from '@/lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'success' | 'warning' | 'error' | 'info'
}

const variantStyles: Record<string, string> = {
  default: 'bg-[#1f2937] text-[#f9fafb]',
  outline: 'border border-[#1f2937] text-[#9ca3af]',
  success: 'bg-emerald-900/40 text-emerald-400 border border-emerald-800',
  warning: 'bg-yellow-900/40 text-yellow-400 border border-yellow-800',
  error: 'bg-red-900/40 text-red-400 border border-red-800',
  info: 'bg-blue-900/40 text-blue-400 border border-blue-800',
}

export function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variantStyles[variant],
        className
      )}
      {...props}
    />
  )
}
