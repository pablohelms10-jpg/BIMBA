import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number // 0-100
  showLabel?: boolean
  color?: 'blue' | 'green' | 'yellow' | 'red'
}

const colorStyles: Record<string, string> = {
  blue: 'bg-[#3b82f6]',
  green: 'bg-[#10b981]',
  yellow: 'bg-yellow-400',
  red: 'bg-red-500',
}

export function Progress({ className, value, showLabel, color = 'blue', ...props }: ProgressProps) {
  const clamped = Math.min(100, Math.max(0, value))
  return (
    <div className={cn('relative', className)} {...props}>
      <div className="h-2 w-full overflow-hidden rounded-full bg-[#1f2937]">
        <div
          className={cn('h-full rounded-full transition-all duration-500 ease-out', colorStyles[color])}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {showLabel && (
        <span className="mt-1 block text-right text-xs text-[#9ca3af]">{clamped}%</span>
      )}
    </div>
  )
}
