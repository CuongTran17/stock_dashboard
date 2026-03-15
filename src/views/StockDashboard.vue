<template>
  <admin-layout>
    <div class="grid grid-cols-12 gap-4 md:gap-6">
      <!-- Header with connection status -->
      <div class="col-span-12 flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-gray-800 dark:text-white/90">
            Stock Dashboard
          </h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
            VN30 Market Data — DNSE Lightspeed
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Dữ liệu cập nhật lần cuối: {{ formattedLastDataSync }}
          </p>
        </div>
        <ConnectionStatus :connected="isConnected" :last-update="lastRefresh" />
      </div>

      <div
        v-if="isLoading"
        class="col-span-12 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-700 dark:border-brand-800 dark:bg-brand-500/10 dark:text-brand-300"
      >
        Loading latest market data...
      </div>

      <div
        v-if="error"
        class="col-span-12 rounded-xl border border-warning-200 bg-warning-50 px-4 py-3 text-sm text-warning-700 dark:border-warning-800 dark:bg-warning-500/10 dark:text-warning-300"
      >
        {{ error }}
      </div>

      <!-- Top Gainers / Top Losers -->
      <div class="col-span-12 rounded-2xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-white/[0.03]">
        <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">Cổ Phiếu Tiêu Biểu VN30</h2>
          <div class="inline-flex items-center gap-1 rounded-xl bg-gray-100 p-1 dark:bg-gray-800">
            <button
              class="rounded-lg px-4 py-1.5 text-sm font-medium transition-colors"
              :class="
                activeTab === 'gainers'
                  ? 'bg-success-500 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              "
              @click="activeTab = 'gainers'"
            >
              ↑ Top Tăng
            </button>
            <button
              class="rounded-lg px-4 py-1.5 text-sm font-medium transition-colors"
              :class="
                activeTab === 'losers'
                  ? 'bg-error-500 text-white shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              "
              @click="activeTab = 'losers'"
            >
              ↓ Top Giảm
            </button>
          </div>
        </div>

        <div v-if="snapshotsLoading" class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
          Đang tải dữ liệu...
        </div>

        <div v-else-if="displayedStocks.length === 0" class="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
          Không có dữ liệu.
        </div>

        <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
          <button
            v-for="stock in displayedStocks"
            :key="stock.symbol"
            class="flex items-center justify-between rounded-xl border border-gray-100 bg-gray-50 px-4 py-3 text-left transition-all hover:-translate-y-0.5 hover:shadow-md dark:border-gray-800 dark:bg-white/[0.03]"
            @click="navigateToStock(stock.symbol)"
          >
            <div class="flex items-center gap-3">
              <div
                class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white"
                :style="{ backgroundColor: symbolColor(stock.symbol) }"
              >
                {{ stock.symbol.charAt(0) }}
              </div>
              <div>
                <p class="text-sm font-semibold text-gray-800 dark:text-white/90">{{ stock.symbol }}</p>
                <p class="max-w-[100px] truncate text-xs text-gray-500 dark:text-gray-400">{{ stock.companyName || stock.symbol }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-sm font-semibold text-gray-800 dark:text-white/90">
                {{ formatPrice(stock.price) }}
              </p>
              <p
                class="text-xs font-medium"
                :class="stock.changePercent >= 0 ? 'text-success-600' : 'text-error-600'"
              >
                {{ stock.changePercent >= 0 ? '+' : '' }}{{ stock.changePercent.toFixed(2) }}%
              </p>
            </div>
          </button>
        </div>
      </div>

      <!-- Portfolio Performance Chart -->
      <div class="col-span-12 xl:col-span-8">
        <PortfolioChart :symbol="selectedSymbol" />
      </div>

      <!-- Dividend Chart -->
      <div class="col-span-12 xl:col-span-4">
        <DividendChart />
      </div>

      <!-- Watchlist -->
      <div class="col-span-12 xl:col-span-4">
        <StockWatchlist
          :stocks="watchlistStocks"
          @select="onSelectStock"
          @add="addToWatchlist"
          @remove="removeFromWatchlist"
        />
      </div>

      <!-- Market Overview Table -->
      <div class="col-span-12 xl:col-span-8">
        <MarketOverview :stocks="allStocksArray" @select="onSelectStock" />
      </div>

      <!-- Technical Analysis Chart (full width) -->
      <div class="col-span-12">
        <TechnicalAnalysisChart
          :symbol="selectedSymbol"
          :fetch-technical="getTechnicalAnalysis"
        />
      </div>
    </div>
  </admin-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import PortfolioChart from '@/components/stock/PortfolioChart.vue'
import DividendChart from '@/components/stock/DividendChart.vue'
import StockWatchlist from '@/components/stock/StockWatchlist.vue'
import MarketOverview from '@/components/stock/MarketOverview.vue'
import ConnectionStatus from '@/components/stock/ConnectionStatus.vue'
import TechnicalAnalysisChart from '@/components/stock/TechnicalAnalysisChart.vue'
import { useStockData, VN30_TICKERS } from '@/composables/useStockData'
import { stockBackendApi, type StockSnapshot } from '@/services/stockBackendApi'

const router = useRouter()

const {
  stocks,
  watchlistStocks,
  isConnected,
  isLoading,
  error,
  lastRefresh,
  lastDataSyncAt,
  fetchInitialData,
  connectRealtime,
  startPolling,
  addToWatchlist,
  removeFromWatchlist,
  getTechnicalAnalysis,
  cleanup,
} = useStockData()

const selectedSymbol = ref('FPT')

// ── Snapshot data for top movers ──────────────────────────────────────────────
type FilterTab = 'gainers' | 'losers'

const snapshots = ref<StockSnapshot[]>([])
const snapshotsLoading = ref(false)
const activeTab = ref<FilterTab>('gainers')

const topGainers = computed(() =>
  [...snapshots.value]
    .filter((s) => s.price > 0 && s.changePercent >= 0)
    .sort((a, b) => b.changePercent - a.changePercent)
    .slice(0, 10),
)

const topLosers = computed(() =>
  [...snapshots.value]
    .filter((s) => s.price > 0 && s.changePercent < 0)
    .sort((a, b) => a.changePercent - b.changePercent)
    .slice(0, 10),
)

const displayedStocks = computed(() =>
  activeTab.value === 'gainers' ? topGainers.value : topLosers.value,
)

async function loadSnapshots(): Promise<void> {
  snapshotsLoading.value = true
  try {
    const res = await stockBackendApi.getSnapshots(VN30_TICKERS, false)
    snapshots.value = res.data
  } catch {
    snapshots.value = []
  } finally {
    snapshotsLoading.value = false
  }
}

function navigateToStock(symbol: string): void {
  void router.push(`/stocks/${symbol}`)
}

const SYMBOL_COLORS: Record<string, string> = {
  FPT: '#F37021', VNM: '#0072BC', VCB: '#00553E', HPG: '#E31E24',
  MBB: '#1B3C87', TCB: '#E31E24', VIC: '#003366', MSN: '#E31E24',
}
const COLOR_PALETTE = ['#465FFF', '#0EA5E9', '#22C55E', '#F59E0B', '#EF4444', '#06B6D4', '#8B5CF6', '#14B8A6']

function symbolColor(symbol: string): string {
  const s = symbol.toUpperCase()
  if (SYMBOL_COLORS[s]) return SYMBOL_COLORS[s]
  let h = 0
  for (const c of s) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return COLOR_PALETTE[h % COLOR_PALETTE.length]
}

function formatPrice(price: number): string {
  return new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 }).format(price)
}

const allStocksArray = computed(() => {
  return Object.values(stocks).filter((s) => s.price > 0)
})

const formattedLastDataSync = computed(() => {
  if (!lastDataSyncAt.value) {
    return 'Chưa có dữ liệu'
  }

  const dt = new Date(lastDataSyncAt.value)
  if (Number.isNaN(dt.getTime())) {
    return lastDataSyncAt.value
  }

  return dt.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
})

function onSelectStock(symbol: string) {
  selectedSymbol.value = symbol
}

onMounted(async () => {
  // 1. Tải dữ liệu ban đầu từ REST API
  await fetchInitialData()
  void loadSnapshots()

  // 2. Kết nối WebSocket cho real-time
  try {
    connectRealtime()
  } catch {
    // Fallback: polling mỗi 5 giây
    startPolling(5000)
  }
})

onUnmounted(() => {
  cleanup()
})
</script>
