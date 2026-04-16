/**
 * Stock Backend API Service
 * =========================
 * Kết nối Vue frontend với FastAPI backend.
 */

function normalizeBackendUrl(rawUrl?: string): string {
  const value = (rawUrl || '').trim()
  if (!value) return 'http://127.0.0.1:8000'
  if (/^https?:\/\//i.test(value)) return value.replace(/\/+$/, '')
  if (value.startsWith(':')) return `http://127.0.0.1${value}`
  return `http://${value}`.replace(/\/+$/, '')
}

const BACKEND_URL = normalizeBackendUrl(import.meta.env.VITE_BACKEND_URL)

export interface HealthResponse {
  status: 'ok' | 'error'
  database: string
}

interface ApiMeta {
  source?: string
  last_synced_at?: string
}

export interface HistoricalRecord {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface TechnicalIndicators {
  sma_20: number[]
  sma_50: number[]
  sma_200: number[]
  ema_12: number[]
  ema_26: number[]
  rsi_14: number[]
  macd_line: number[]
  macd_signal: number[]
  macd_histogram: number[]
  bb_upper: number[]
  bb_middle: number[]
  bb_lower: number[]
  stoch_k: number[]
  stoch_d: number[]
  atr_14: number[]
  obv: number[]
}

export interface TradingSignals {
  rsi: 'oversold' | 'overbought' | 'neutral'
  macd: 'bullish' | 'bearish'
  golden_cross: boolean
  price_vs_sma200: 'above' | 'below'
  summary: 'strong_buy' | 'buy' | 'neutral' | 'sell' | 'strong_sell'
}

export interface TechnicalResponse extends ApiMeta {
  symbol: string
  count: number
  ohlcv: {
    time: string[]
    open: number[]
    high: number[]
    low: number[]
    close: number[]
    volume: number[]
  }
  indicators: TechnicalIndicators
  signals: TradingSignals
}

export interface HistoryResponse extends ApiMeta {
  symbol: string
  count: number
  data: HistoricalRecord[]
}

export interface IntradayResponse extends ApiMeta {
  symbol: string
  count: number
  ticks_count: number
  data: HistoricalRecord[]
  is_in_session: boolean
  refreshed: boolean
  forced: boolean
}

export interface OrderTick {
  id: string
  symbol: string
  time: string
  price: number
  volume: number
  match_type: string
}

export interface TicksResponse extends ApiMeta {
  symbol: string
  count: number
  ticks: OrderTick[]
  is_in_session: boolean
  refreshed: boolean
}

export interface FinancialsResponse extends ApiMeta {
  symbol: string
  type: 'income' | 'balance' | 'cashflow' | 'ratios'
  count: number
  data: Record<string, unknown>[]
}

export interface MarketIndicesResponse extends ApiMeta {
  count: number
  data: MarketIndexQuote[]
}

export interface MarketIndexQuote {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  time: string
}

export interface MarketIndexHistoryResponse extends ApiMeta {
  symbol: string
  name: string
  count: number
  data: HistoricalRecord[]
}

export interface StockSnapshot {
  symbol: string
  companyName: string
  price: number
  change: number
  changePercent: number
  volume: number
  high: number
  low: number
  open: number
  refPrice: number
  lastUpdate: string
  syncedAt?: string
}

export interface SnapshotsResponse extends ApiMeta {
  count: number
  data: StockSnapshot[]
  cached_at: string
}

export interface MarketNewsItem {
  id: string
  symbol: string
  symbols: string[]
  source: string
  title: string
  summary: string
  publish_time: string
  time: string
  url: string
  impact: 'high' | 'medium' | 'low'
}

export interface MarketNewsResponse extends ApiMeta {
  count: number
  symbols: string[]
  data: MarketNewsItem[]
  cached_at: string
}

export interface MarketEventItem {
  id: string
  symbol: string
  date: string
  title: string
  description: string
}

export interface MarketEventsResponse extends ApiMeta {
  count: number
  symbols: string[]
  data: MarketEventItem[]
  cached_at: string
}

export interface SaveQuotePayload {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume: number
  high: number
  low: number
  open: number
  time: string
}

export type CompanyOverview = Record<string, unknown>

class StockBackendApi {
  private baseUrl: string

  constructor(baseUrl: string = BACKEND_URL) {
    this.baseUrl = baseUrl
  }

  private async fetch<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers || {}),
      },
      ...init,
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(`API Error ${response.status}: ${body}`)
    }

    return response.json() as Promise<T>
  }

  private buildQuery(params: Record<string, string | number | boolean | undefined>): string {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        query.set(key, String(value))
      }
    })
    const str = query.toString()
    return str ? `?${str}` : ''
  }

  async checkHealth(): Promise<HealthResponse> {
    return this.fetch<HealthResponse>('/api/health')
  }

  async getStockList(): Promise<string[]> {
    const data = await this.fetch<{ tickers: string[] }>('/api/stocks')
    return data.tickers
  }

  async getCompanyOverview(
    symbol: string,
    refresh: boolean = false,
  ): Promise<CompanyOverview> {
    const query = this.buildQuery({ refresh: refresh || undefined })
    return this.fetch<CompanyOverview>(`/api/stocks/${symbol.toUpperCase()}/overview${query}`)
  }

  async getHistory(
    symbol: string,
    startDate?: string,
    endDate?: string,
    limit: number = 365,
    refresh: boolean = false,
  ): Promise<HistoryResponse> {
    const query = this.buildQuery({
      start_date: startDate,
      end_date: endDate,
      limit,
      refresh: refresh || undefined,
    })

    return this.fetch<HistoryResponse>(`/api/stocks/${symbol.toUpperCase()}/history${query}`)
  }

  async getIntraday(
    symbol: string,
    limit: number = 320,
    refresh: boolean = false,
    force: boolean = false,
  ): Promise<IntradayResponse> {
    const query = this.buildQuery({
      limit,
      refresh: refresh || undefined,
      force: force || undefined,
    })

    return this.fetch<IntradayResponse>(`/api/stocks/${symbol.toUpperCase()}/intraday${query}`)
  }

  async getOrderLog(
    symbol: string,
    limit: number = 100,
    refresh: boolean = false,
    force: boolean = false,
  ): Promise<TicksResponse> {
    const query = this.buildQuery({
      limit,
      refresh: refresh || undefined,
      force: force || undefined,
    })

    return this.fetch<TicksResponse>(`/api/stocks/${symbol.toUpperCase()}/ticks${query}`)
  }

  async getTechnicalAnalysis(
    symbol: string,
    startDate?: string,
    endDate?: string,
    limit: number = 365,
    refresh: boolean = false,
  ): Promise<TechnicalResponse> {
    const query = this.buildQuery({
      start_date: startDate,
      end_date: endDate,
      limit,
      refresh: refresh || undefined,
    })

    return this.fetch<TechnicalResponse>(`/api/stocks/${symbol.toUpperCase()}/technical${query}`)
  }

  async getFinancials(
    symbol: string,
    reportType: 'income' | 'balance' | 'cashflow' | 'ratios' = 'income',
    refresh: boolean = false,
  ): Promise<FinancialsResponse> {
    const query = this.buildQuery({ report_type: reportType, refresh: refresh || undefined })
    return this.fetch<FinancialsResponse>(`/api/stocks/${symbol.toUpperCase()}/financials${query}`)
  }

  async getMarketIndices(
    startDate?: string,
    endDate?: string,
    limit: number = 365,
    refresh: boolean = false,
  ): Promise<MarketIndicesResponse> {
    const query = this.buildQuery({
      start_date: startDate,
      end_date: endDate,
      limit,
      refresh: refresh || undefined,
    })

    return this.fetch<MarketIndicesResponse>(`/api/market-indices${query}`)
  }

  async getMarketIndexHistory(
    indexSymbol: string,
    startDate?: string,
    endDate?: string,
    limit: number = 365,
    refresh: boolean = false,
  ): Promise<MarketIndexHistoryResponse> {
    const query = this.buildQuery({
      start_date: startDate,
      end_date: endDate,
      limit,
      refresh: refresh || undefined,
    })

    return this.fetch<MarketIndexHistoryResponse>(`/api/market-indices/${indexSymbol.toUpperCase()}/history${query}`)
  }

  async getSnapshots(
    symbols: string[],
    refresh: boolean = false,
  ): Promise<SnapshotsResponse> {
    const normalized = symbols
      .map((symbol) => symbol.trim().toUpperCase())
      .filter((symbol) => symbol.length > 0)

    const query = this.buildQuery({
      symbols: normalized.length > 0 ? normalized.join(',') : undefined,
      refresh: refresh || undefined,
    })

    return this.fetch<SnapshotsResponse>(`/api/stocks/snapshots${query}`)
  }

  async getMarketNews(
    symbols?: string[],
    limit: number = 24,
    refresh: boolean = false,
  ): Promise<MarketNewsResponse> {
    const normalized = (symbols || [])
      .map((symbol) => symbol.trim().toUpperCase())
      .filter((symbol) => symbol.length > 0)

    const query = this.buildQuery({
      symbols: normalized.length > 0 ? normalized.join(',') : undefined,
      limit,
      refresh: refresh || undefined,
    })

    return this.fetch<MarketNewsResponse>(`/api/news${query}`)
  }

  async getMarketEvents(
    symbols?: string[],
    limit: number = 24,
    refresh: boolean = false,
  ): Promise<MarketEventsResponse> {
    const normalized = (symbols || [])
      .map((symbol) => symbol.trim().toUpperCase())
      .filter((symbol) => symbol.length > 0)

    const query = this.buildQuery({
      symbols: normalized.length > 0 ? normalized.join(',') : undefined,
      limit,
      refresh: refresh || undefined,
    })

    return this.fetch<MarketEventsResponse>(`/api/events${query}`)
  }

  async saveRealtimeQuotes(quotes: SaveQuotePayload[]): Promise<{ saved: number }> {
    return this.fetch<{ saved: number }>('/api/dnse/save-quotes', {
      method: 'POST',
      body: JSON.stringify(quotes),
    })
  }
}

export const stockBackendApi = new StockBackendApi()
export default stockBackendApi
