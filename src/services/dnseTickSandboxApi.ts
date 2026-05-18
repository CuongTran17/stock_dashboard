import { backendFetch } from './httpClient'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''

export interface DnseTick {
  symbol: string
  price: number | null
  volume: number | null
  trade_time: string | null
  source: 'dnse'
  latency_ms?: number
  raw: Record<string, unknown>
}

export interface DnseTickResponse {
  status: 'ok' | 'error' | 'not_configured'
  source: 'dnse'
  requested_at?: string
  symbols: string[]
  ticks: DnseTick[]
  errors: Record<string, string>
  latency_ms: number
}

export interface DnseTickStatus {
  status: 'configured' | 'not_configured'
  configured: boolean
  base_url: string
  board_id: string
  poll_interval_ms: number
  endpoint: string
  auth: string
}

export async function getLatestTicks(symbols: string): Promise<DnseTickResponse> {
  const query = new URLSearchParams({ symbols })
  return backendFetch<DnseTickResponse>(BACKEND_URL, `/api/dnse/ticks/latest?${query.toString()}`, undefined, {
    timeoutMs: 12000,
    retries: 0,
  })
}

export async function getDnseTickStatus(): Promise<DnseTickStatus> {
  return backendFetch<DnseTickStatus>(BACKEND_URL, '/api/dnse/ticks/status', undefined, {
    timeoutMs: 8000,
    retries: 1,
  })
}
