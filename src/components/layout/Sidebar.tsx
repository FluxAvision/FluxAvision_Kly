'use client'

import Image from 'next/image'

import {
  LayoutDashboard,
  Camera,
  BarChart3,
  Settings,
  Monitor,
  Video,
  Presentation,
} from 'lucide-react'

interface SidebarProps {
  activePage: string
  onPageChange: (page: string) => void
  onNavigateToScreen?: () => void
}

const navItems = [
  { id: 'dashboard', label: '仪表盘', icon: LayoutDashboard },
  { id: 'devices', label: '设备管理', icon: Camera },
  { id: 'history', label: '历史数据', icon: BarChart3 },
]

const settingsItems = [
  { id: 'settings', label: '系统设置', icon: Settings },
  { id: 'large-screen-settings', label: '大屏设置', icon: Presentation },
]

export default function Sidebar({
  activePage,
  onPageChange,
  onNavigateToScreen,
}: SidebarProps) {
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[240px] bg-[#0a192f] border-r border-[#1e293b] flex flex-col z-50">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 h-16 border-b border-[#1e293b] flex-shrink-0">
        <Image src="/logo.png" alt="FluxaVision" width={32} height={32} className="rounded-lg" />
        <span className="text-lg font-bold text-white tracking-wide">
          FluxAvision
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        <p className="px-3 py-1.5 text-xs text-[#8892a0]/60 font-medium uppercase tracking-wider">
          数据概览
        </p>
        {navItems.map((item) => {
          const isActive = activePage === item.id
          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                isActive
                  ? 'sidebar-active-indicator bg-[#172a45] text-[#00d9ff]'
                  : 'text-[#8892a0] hover:bg-[#172a45] hover:text-white'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              <span>{item.label}</span>
            </button>
          )
        })}

        <div className="my-3 mx-3 border-t border-[#1e293b]" />

        <p className="px-3 py-1.5 text-xs text-[#8892a0]/60 font-medium uppercase tracking-wider">
          系统管理
        </p>
        {settingsItems.map((item) => {
          const isActive = activePage === item.id
          return (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                isActive
                  ? 'sidebar-active-indicator bg-[#172a45] text-[#00d9ff]'
                  : 'text-[#8892a0] hover:bg-[#172a45] hover:text-white'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      {/* Large Screen Button */}
      <div className="px-3 pb-2 flex-shrink-0">
        {onNavigateToScreen && (
          <button
            onClick={onNavigateToScreen}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[#8892a0] hover:bg-[#172a45] hover:text-white transition-all duration-200 cursor-pointer border border-dashed border-[#1e293b] hover:border-[#00d9ff]/30"
          >
            <Monitor className="w-5 h-5 flex-shrink-0" />
            <span>大屏模式</span>
          </button>
        )}
      </div>

      {/* Version */}
      <div className="px-6 pb-4 flex-shrink-0">
        <p className="text-xs text-[#8892a0]/50">FluxAvision v2.1.0</p>
      </div>
    </aside>
  )
}
