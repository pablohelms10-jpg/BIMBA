'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface TabsContextValue {
  activeTab: string
  setActiveTab: (tab: string) => void
}

const TabsContext = React.createContext<TabsContextValue>({ activeTab: '', setActiveTab: () => {} })

export interface TabsProps {
  defaultValue: string
  children: React.ReactNode
  className?: string
  onValueChange?: (value: string) => void
}

export function Tabs({ defaultValue, children, className, onValueChange }: TabsProps) {
  const [activeTab, setActiveTab] = React.useState(defaultValue)

  const handleSetActiveTab = React.useCallback(
    (tab: string) => {
      setActiveTab(tab)
      onValueChange?.(tab)
    },
    [onValueChange]
  )

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleSetActiveTab }}>
      <div className={cn('w-full', className)}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        'inline-flex items-center rounded-lg bg-[#111827] p-1 border border-[#1f2937]',
        className
      )}
    >
      {children}
    </div>
  )
}

export function TabsTrigger({
  value,
  children,
  className,
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const { activeTab, setActiveTab } = React.useContext(TabsContext)
  const isActive = activeTab === value

  return (
    <button
      onClick={() => setActiveTab(value)}
      className={cn(
        'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-all',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3b82f6]',
        isActive
          ? 'bg-[#3b82f6] text-white shadow'
          : 'text-[#9ca3af] hover:text-[#f9fafb] hover:bg-[#1f2937]',
        className
      )}
    >
      {children}
    </button>
  )
}

export function TabsContent({
  value,
  children,
  className,
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const { activeTab } = React.useContext(TabsContext)
  if (activeTab !== value) return null
  return <div className={cn('mt-4', className)}>{children}</div>
}
