'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Shield, KeyRound, ArrowRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface LoginPageProps {
  onLogin: () => void
  hasPassword: boolean
  isLicensed: boolean
  onActivateLicense: (code: string) => void
  hardwareFingerprint: string
}

export default function LoginPage({
  onLogin,
  hasPassword,
  isLicensed,
  onActivateLicense,
  hardwareFingerprint,
}: LoginPageProps) {
  const [password, setPassword] = useState('')
  const [activatingCode, setActivatingCode] = useState('')
  const [activating, setActivating] = useState(false)
  const [error, setError] = useState('')

  const handleActivate = async () => {
    if (!activatingCode.trim()) return
    setActivating(true)
    setError('')
    try {
      onActivateLicense(activatingCode.trim())
    } catch {
      setError('激活失败，请检查激活码')
    } finally {
      setActivating(false)
    }
  }

  const handleLogin = () => {
    if (hasPassword && !password) {
      setError('请输入密码')
      return
    }
    setError('')
    onLogin()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (!isLicensed) {
        handleActivate()
      } else {
        handleLogin()
      }
    }
  }

  return (
    <div className="min-h-screen bg-[#0a192f] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <Image src="/logo.png" alt="FluxaVision" width={64} height={64} className="rounded-2xl" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            FluxaVision客流统计系统
          </h1>
          <p className="text-sm text-[#8892a0]">智能客流分析与管理平台</p>
        </div>

        {/* Card */}
        <div className="bg-[#112240] border border-[#1e293b] rounded-xl p-8">
          {!isLicensed ? (
            /* License Activation */
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-2">
                <Shield className="w-5 h-5 text-[#ff9500]" />
                <h2 className="text-lg font-medium text-white">系统激活</h2>
              </div>
              <p className="text-sm text-[#8892a0]">
                请先激活系统License以使用全部功能
              </p>

              <div className="grid gap-2">
                <Label className="text-[#8892a0] text-xs">硬件指纹</Label>
                <div className="bg-[#0a192f] border border-[#1e293b] rounded-lg px-3 py-2 font-mono text-xs text-[#8892a0] break-all">
                  {hardwareFingerprint || '正在生成...'}
                </div>
              </div>

              <div className="grid gap-2">
                <Label className="text-[#8892a0] text-xs">激活码</Label>
                <Textarea
                  value={activatingCode}
                  onChange={(e) => setActivatingCode(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="请输入激活码..."
                  className="bg-[#0a192f] border-[#1e293b] min-h-[100px] font-mono text-xs resize-none"
                />
              </div>

              {error && (
                <p className="text-sm text-[#ef4444]">{error}</p>
              )}

              <Button
                onClick={handleActivate}
                disabled={activating || !activatingCode.trim()}
                className="w-full bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80"
              >
                {activating ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Shield className="w-4 h-4 mr-2" />
                )}
                激活系统
              </Button>
            </div>
          ) : hasPassword ? (
            /* Password Login */
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-2">
                <KeyRound className="w-5 h-5 text-[#00d9ff]" />
                <h2 className="text-lg font-medium text-white">登录系统</h2>
              </div>

              <div className="grid gap-2">
                <Label className="text-[#8892a0]">登录密码</Label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    setError('')
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="请输入登录密码"
                  className="bg-[#0a192f] border-[#1e293b]"
                  autoFocus
                />
              </div>

              {error && (
                <p className="text-sm text-[#ef4444]">{error}</p>
              )}

              <Button
                onClick={handleLogin}
                className="w-full bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80"
              >
                <span>进入系统</span>
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          ) : (
            /* No Password - Direct Entry */
            <div className="space-y-6 text-center">
              <div className="flex items-center justify-center gap-3 mb-2">
                <Shield className="w-5 h-5 text-[#00ff88]" />
                <h2 className="text-lg font-medium text-white">系统已就绪</h2>
              </div>
              <p className="text-sm text-[#8892a0]">系统未设置登录密码，点击下方按钮进入</p>

              <Button
                onClick={handleLogin}
                className="w-full bg-[#00d9ff] text-[#0a192f] hover:bg-[#00d9ff]/80"
              >
                <span>进入系统</span>
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-[#8892a0]/50 mt-6">
          FluxaVision v2.1.0 · 客流统计系统
        </p>
      </div>
    </div>
  )
}
