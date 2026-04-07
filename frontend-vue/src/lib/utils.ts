import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function generateRtspUrl(
  model: string,
  ip: string,
  port: number,
  username: string,
  password: string
): string {
  if (!ip) return ''
  const cred = password ? `${username}:${password}` : username
  if (model === '海康威视') {
    return `rtsp://${cred}@${ip}:${port}/Streaming/Channels/101`
  }
  if (model === '大华') {
    return `rtsp://${cred}@${ip}:${port}/cam/realmonitor?channel=1&subtype=0`
  }
  return `rtsp://${cred}@${ip}:${port}/stream1`
}
