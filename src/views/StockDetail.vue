<template>
  <AdminLayout>
    <div class="space-y-6">
      <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">
            {{ symbol }} - {{ displayName }}
          </h1>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Price, valuation metrics, order book, and financial statements.
          </p>
        </div>

        <div class="flex flex-col gap-2 md:items-end">
          <div class="w-full md:w-[180px]">
            <label class="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
              VN30 Symbol
            </label>
            <select
              v-model="symbolPicker"
              class="w-full rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
              @change="onSymbolPickerChange"
            >
              <option
                v-for="ticker in vn30Tickers"
                :key="ticker"
                :value="ticker"
              >
                {{ ticker }}
              </option>
            </select>
          </div>

          <button
            class="inline-flex items-center justify-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700 transition hover:bg-brand-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-brand-700/50 dark:bg-brand-500/10 dark:text-brand-300"
            :disabled="manualRefreshing || loadingOverview || loadingFinancials"
            @click="onRefreshClick"
          >
            <span
              v-if="manualRefreshing"
              class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
            ></span>
            <span>{{ manualRefreshing ? 'Đang cập nhật...' : 'Tải lại dữ liệu' }}</span>
          </button>

          <div
            class="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm"
            :class="
              selectedStock && selectedStock.changePercent >= 0
                ? 'border-success-200 bg-success-50 text-success-700 dark:border-success-800 dark:bg-success-500/10 dark:text-success-400'
                : 'border-error-200 bg-error-50 text-error-700 dark:border-error-800 dark:bg-error-500/10 dark:text-error-400'
            "
          >
            <span class="font-semibold">{{ formatPrice(selectedStock?.price || 0) }}</span>
            <span>
              {{ selectedStock && selectedStock.changePercent >= 0 ? '+' : ''
              }}{{ (selectedStock?.changePercent || 0).toFixed(2) }}%
            </span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-12 gap-4 md:gap-6">
        <section class="col-span-12 xl:col-span-8">
          <PortfolioChart :symbol="symbol" :historical-data="chartHistory" />
        </section>

        <section
          class="col-span-12 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] xl:col-span-4"
        >
          <h2 class="mb-4 text-lg font-semibold text-gray-800 dark:text-white/90">Valuation Snapshot</h2>
          <div class="space-y-3">
            <div
              v-for="metric in valuationCards"
              :key="metric.label"
              class="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2 dark:border-gray-800"
            >
              <p class="text-sm text-gray-600 dark:text-gray-400">{{ metric.label }}</p>
              <p class="text-sm font-semibold text-gray-800 dark:text-white/90">{{ metric.value }}</p>
            </div>
          </div>
        </section>

        <section class="col-span-12">
          <TradingViewChart :symbol="symbol" :theme="tradingViewTheme" :historical-data="historySeries">
            <button
              v-for="tf in CHART_TIMEFRAMES"
              :key="tf.value"
              class="rounded-lg px-3 py-1.5 text-xs font-medium transition-colors"
              :class="
                chartTimeframe === tf.value
                  ? 'bg-brand-500 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'
              "
              @click="chartTimeframe = tf.value"
            >
              {{ tf.label }}
            </button>
          </TradingViewChart>
        </section>

        <section
          class="col-span-12 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] xl:col-span-4"
        >
          <h2 class="mb-4 text-lg font-semibold text-gray-800 dark:text-white/90">Order Book</h2>

          <div class="rounded-xl border border-dashed border-gray-200 px-3 py-8 text-center text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
            Chưa có dữ liệu sổ lệnh từ backend.
          </div>
        </section>

        <section class="col-span-12 xl:col-span-8">
          <TechnicalAnalysisChart :symbol="symbol" :fetch-technical="getTechnicalAnalysis" :refresh-token="technicalRefreshToken" />
        </section>

        <section
          class="col-span-12 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]"
        >
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">Financial Statements</h2>
            <div class="inline-flex w-fit items-center gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
              <button
                v-for="type in reportTypes"
                :key="type.value"
                class="rounded-md px-3 py-1.5 text-sm"
                :class="
                  activeReportType === type.value
                    ? 'bg-white text-gray-900 shadow-theme-xs dark:bg-gray-900 dark:text-white'
                    : 'text-gray-500 dark:text-gray-400'
                "
                @click="changeReportType(type.value)"
              >
                {{ type.label }}
              </button>
            </div>
          </div>

          <div v-if="loadingFinancials" class="py-6 text-sm text-gray-500 dark:text-gray-400">
            Loading financial statements...
          </div>

          <div v-else-if="financialPreviewRows.length === 0" class="py-6 text-sm text-gray-500 dark:text-gray-400">
            No financial data available for this symbol.
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700">
                  <th
                    v-for="column in financialColumns"
                    :key="column"
                    class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400"
                  >
                    {{ formatColumnName(column) }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, index) in financialPreviewRows"
                  :key="`row-${index}`"
                  class="border-b border-gray-100 dark:border-gray-800"
                >
                  <td
                    v-for="column in financialColumns"
                    :key="`${index}-${column}`"
                    class="px-3 py-2 text-gray-700 dark:text-gray-300"
                  >
                    {{ formatCell(row[column]) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import PortfolioChart from '@/components/stock/PortfolioChart.vue'
import TechnicalAnalysisChart from '@/components/stock/TechnicalAnalysisChart.vue'
import TradingViewChart from '@/components/stock/TradingViewChart.vue'
import { VN30_TICKERS, useStockData } from '@/composables/useStockData'
import { stockBackendApi, type CompanyOverview } from '@/services/stockBackendApi'

type FinancialType = 'income' | 'balance' | 'cashflow' | 'ratios'

const CHART_TIMEFRAMES = [
  { label: '1T', value: '1m' },
  { label: '3T', value: '3m' },
  { label: '6T', value: '6m' },
  { label: '1N', value: '1y' },
] as const

type ChartTimeframe = (typeof CHART_TIMEFRAMES)[number]['value']

function timeframeToLimit(tf: ChartTimeframe | string): number {
  if (tf === '1m') return 30
  if (tf === '3m') return 90
  if (tf === '6m') return 180
  return 365
}

type HistoricalCandle = {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

const route = useRoute()
const router = useRouter()

const {
  stocks,
  fetchInitialData,
  connectRealtime,
  startPolling,
  addToWatchlist,
  getTechnicalAnalysis,
  cleanup,
} = useStockData()

const historySeries = ref<HistoricalCandle[]>([])
const chartTimeframe = ref<string>('1y')
const overview = ref<CompanyOverview | null>(null)
const financialRows = ref<Record<string, unknown>[]>([])
const loadingOverview = ref(false)
const loadingFinancials = ref(false)
const manualRefreshing = ref(false)
const technicalRefreshToken = ref(0)
const activeReportType = ref<FinancialType>('income')
const symbolPicker = ref('FPT')

const vn30Tickers = VN30_TICKERS

const reportTypes: Array<{ label: string; value: FinancialType }> = [
  { label: 'Income', value: 'income' },
  { label: 'Balance', value: 'balance' },
  { label: 'Cashflow', value: 'cashflow' },
  { label: 'Ratios', value: 'ratios' },
]

const symbol = computed(() => {
  const value = route.params.symbol
  if (Array.isArray(value)) {
    return (value[0] || 'FPT').toUpperCase()
  }
  return String(value || 'FPT').toUpperCase()
})

const selectedStock = computed(() => stocks[symbol.value] || null)
const tradingViewTheme = computed<'light' | 'dark'>(() => (
  document.documentElement.classList.contains('dark') ? 'dark' : 'light'
))

const displayName = computed(() => {
  if (selectedStock.value?.companyName) return selectedStock.value.companyName

  const nameKeys = ['company_name', 'companyName', 'name', 'company', 'short_name']
  for (const key of nameKeys) {
    const value = overview.value?.[key]
    if (typeof value === 'string' && value.trim()) {
      return value
    }
  }

  return symbol.value
})

const chartHistory = computed(() => historySeries.value.map((item) => ({
  time: item.time,
  close: item.close,
})))

const valuationCards = computed(() => [
  { label: 'P/E', value: formatMetric(readNumber(overview.value, ['pe', 'p_e', 'pe_ratio', 'pe_ttm'])) },
  { label: 'P/B', value: formatMetric(readNumber(overview.value, ['pb', 'p_b', 'pb_ratio', 'pb_ttm'])) },
  { label: 'EPS', value: formatMetric(readNumber(overview.value, ['eps', 'eps_ttm'])) },
  { label: 'ROE', value: formatPercent(readNumber(overview.value, ['roe', 'roe_ttm'])) },
  { label: 'ROA', value: formatPercent(readNumber(overview.value, ['roa', 'roa_ttm'])) },
  { label: 'Market Cap', value: formatLargeValue(readNumber(overview.value, ['market_cap', 'marketCap', 'marketCapitalization'])) },
])

const financialColumns = computed(() => {
  const first = financialRows.value[0]
  return first ? Object.keys(first).slice(0, 6) : []
})

const financialPreviewRows = computed(() => financialRows.value.slice(0, 8))

function toNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string') {
    const parsed = Number(value.replace(/,/g, ''))
    if (Number.isFinite(parsed)) return parsed
  }
  return null
}

function readNumber(source: CompanyOverview | null, keys: string[]): number | null {
  if (!source) return null

  for (const key of keys) {
    const value = toNumber(source[key])
    if (value !== null) return value
  }

  return null
}

function formatMetric(value: number | null): string {
  if (value === null) return '-'
  return value.toFixed(2)
}

function formatPercent(value: number | null): string {
  if (value === null) return '-'
  return `${value.toFixed(2)}%`
}

function formatLargeValue(value: number | null): string {
  if (value === null) return '-'
  if (value >= 1_000_000_000_000) {
    return `${(value / 1_000_000_000_000).toFixed(2)}T`
  }
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(2)}B`
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M`
  }
  return new Intl.NumberFormat('vi-VN').format(value)
}

function formatPrice(value: number): string {
  return new Intl.NumberFormat('vi-VN', {
    maximumFractionDigits: 0,
  }).format(value)
}

function formatColumnName(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/^./, (letter) => letter.toUpperCase())
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') {
    if (Math.abs(value) >= 1000) {
      return new Intl.NumberFormat('vi-VN').format(value)
    }
    return value.toFixed(2)
  }
  return String(value)
}

async function loadOverview(forceRefresh: boolean = false): Promise<void> {
  loadingOverview.value = true

  try {
    overview.value = await stockBackendApi.getCompanyOverview(symbol.value, forceRefresh)
  } catch {
    overview.value = null
  } finally {
    loadingOverview.value = false
  }
}

async function loadFinancials(forceRefresh: boolean = false): Promise<void> {
  loadingFinancials.value = true

  try {
    const response = await stockBackendApi.getFinancials(symbol.value, activeReportType.value, forceRefresh)
    financialRows.value = response.data
  } catch {
    financialRows.value = []
  } finally {
    loadingFinancials.value = false
  }
}

async function loadHistory(forceRefresh: boolean = false): Promise<void> {
  const limit = timeframeToLimit(chartTimeframe.value)
  try {
    const response = await stockBackendApi.getHistory(symbol.value, undefined, undefined, limit, forceRefresh)
    historySeries.value = response.data.map((item) => ({
      time: item.time,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
      volume: item.volume,
    }))
  } catch {
    historySeries.value = []
  }
}

async function reloadSymbolData(forceRefresh: boolean = false): Promise<void> {
  addToWatchlist(symbol.value)

  await Promise.all([
    loadOverview(forceRefresh),
    loadFinancials(forceRefresh),
    loadHistory(forceRefresh),
  ])
}

function changeReportType(nextType: FinancialType): void {
  activeReportType.value = nextType
  void loadFinancials()
}

function onSymbolPickerChange(): void {
  const nextSymbol = symbolPicker.value.toUpperCase()
  if (nextSymbol === symbol.value) {
    return
  }

  void router.push(`/stocks/${nextSymbol}`)
}

async function onRefreshClick(): Promise<void> {
  if (manualRefreshing.value) {
    return
  }

  manualRefreshing.value = true
  try {
    await reloadSymbolData(true)
    technicalRefreshToken.value += 1
  } finally {
    manualRefreshing.value = false
  }
}

watch(symbol, (nextSymbol) => {
  symbolPicker.value = nextSymbol
}, { immediate: true })

watch(symbol, () => {
  void reloadSymbolData()
})

watch(chartTimeframe, () => {
  void loadHistory()
})

onMounted(async () => {
  await fetchInitialData()
  await reloadSymbolData()

  try {
    connectRealtime()
  } catch {
    startPolling(5000)
  }
})

onUnmounted(() => {
  cleanup()
})
</script>
