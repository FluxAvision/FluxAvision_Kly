'use client'

import { useEffect, useState } from 'react'
import { Clock } from 'lucide-react'

interface HeaderProps {
  title: string
  storeName?: string
}

export default function Header({ title, storeName }: HeaderProps) {
  const [currentTime, setCurrentTime] = useState('')

  useEffect(() => {
    const update = () => {
      const now = new Date()
      setCurrentTime(
        now.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      )
    }
    update()
    const interval = setInterval(update, 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="h-16 bg-[#0a192f] border-b border-[#1e293b] flex items-center justify-between px-6 flex-shrink-0">
      {/* Left: Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-[#8892a0]">首页</span>
        <span className="text-[#8892a0]">/</span>
        <span className="text-white font-medium">{title}</span>
      </div>

      {/* Right: Store name + Time */}
      <div className="flex items-center gap-4">
        {storeName && (
          <span className="text-xs bg-[#172a45] text-[#00d9ff] px-3 py-1 rounded-full border border-[#1e293b]">
            {storeName}
          </span>
        )}
        <div className="flex items-center gap-2 text-sm text-[#8892a0]">
          <Clock className="w-4 h-4" />
          <span>{currentTime}</span>
        </div>
      </div>
    </header>
  )
}
