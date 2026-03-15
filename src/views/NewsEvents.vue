<template>
  <AdminLayout>
    <div class="space-y-6">
      <div class="flex flex-col gap-2">
        <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">News & Events</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Curated market headlines, corporate events, and live movers.
        </p>
      </div>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
          <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Headlines Today</p>
          <p class="mt-2 text-2xl font-semibold text-gray-800 dark:text-white/90">{{ newsFeed.length }}</p>
        </div>
        <div class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
          <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Upcoming Events</p>
          <p class="mt-2 text-2xl font-semibold text-gray-800 dark:text-white/90">{{ events.length }}</p>
        </div>
        <div class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
          <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">High Impact</p>
          <p class="mt-2 text-2xl font-semibold text-gray-800 dark:text-white/90">{{ highImpactCount }}</p>
        </div>
      </div>

      <div class="grid grid-cols-12 gap-4 md:gap-6">
        <section class="col-span-12 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] xl:col-span-8">
          <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">Market News</h2>
            <div class="inline-flex w-fit items-center gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
              <button
                v-for="option in impactOptions"
                :key="option"
                class="rounded-md px-3 py-1.5 text-sm"
                :class="
                  selectedImpact === option
                    ? 'bg-white text-gray-900 shadow-theme-xs dark:bg-gray-900 dark:text-white'
                    : 'text-gray-500 dark:text-gray-400'
                "
                @click="selectedImpact = option"
              >
                {{ option }}
              </button>
            </div>
          </div>

          <ul v-if="filteredNews.length > 0" class="space-y-3">
            <li
              v-for="item in filteredNews"
              :key="item.id"
              class="rounded-xl border border-gray-100 p-4 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-white/5"
            >
              <div class="flex flex-wrap items-center gap-2">
                <span
                  class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="impactClass(item.impact)"
                >
                  {{ item.impact }}
                </span>
                <span class="text-xs text-gray-500 dark:text-gray-400">{{ item.source }} • {{ item.time }}</span>
              </div>

              <p class="mt-2 font-medium text-gray-800 dark:text-white/90">{{ item.title }}</p>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ item.summary }}</p>

              <div class="mt-2 flex flex-wrap gap-2">
                <button
                  v-for="symbol in item.symbols"
                  :key="`${item.id}-${symbol}`"
                  class="rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                  @click="goToStock(symbol)"
                >
                  {{ symbol }}
                </button>
              </div>
            </li>
          </ul>

          <div v-else class="rounded-xl border border-dashed border-gray-200 px-4 py-8 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
            Chưa có dữ liệu tin tức từ backend.
          </div>
        </section>

        <section class="col-span-12 space-y-4 xl:col-span-4">
          <div class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
            <h2 class="mb-4 text-lg font-semibold text-gray-800 dark:text-white/90">Top Movers</h2>
            <ul class="space-y-2">
              <li
                v-for="stock in topMovers"
                :key="stock.symbol"
                class="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-white/5"
              >
                <button class="font-medium text-gray-800 dark:text-white/90" @click="goToStock(stock.symbol)">
                  {{ stock.symbol }}
                </button>
                <span
                  class="text-sm font-medium"
                  :class="stock.changePercent >= 0 ? 'text-success-600' : 'text-error-600'"
                >
                  {{ stock.changePercent >= 0 ? '+' : '' }}{{ stock.changePercent.toFixed(2) }}%
                </span>
              </li>
            </ul>
          </div>

          <div class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
            <h2 class="mb-4 text-lg font-semibold text-gray-800 dark:text-white/90">Upcoming Events</h2>
            <ul v-if="events.length > 0" class="space-y-3">
              <li
                v-for="event in events"
                :key="event.id"
                class="rounded-lg border border-gray-100 px-3 py-2 dark:border-gray-800"
              >
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ event.date }}</p>
                <p class="mt-1 font-medium text-gray-800 dark:text-white/90">{{ event.title }}</p>
                <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ event.description }}</p>
                <button
                  class="mt-2 rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300"
                  @click="goToStock(event.symbol)"
                >
                  {{ event.symbol }}
                </button>
              </li>
            </ul>

            <div v-else class="rounded-xl border border-dashed border-gray-200 px-3 py-6 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
              Chưa có dữ liệu sự kiện từ backend.
            </div>
          </div>
        </section>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useStockData } from '@/composables/useStockData'
import { stockBackendApi } from '@/services/stockBackendApi'

type ImpactLevel = 'High' | 'Medium' | 'Low'

interface NewsItem {
  id: string
  source: string
  time: string
  impact: ImpactLevel
  title: string
  summary: string
  symbols: string[]
}

interface EventItem {
  id: string
  date: string
  title: string
  description: string
  symbol: string
}

const router = useRouter()

const {
  stocks,
  fetchInitialData,
  connectRealtime,
  startPolling,
  cleanup,
} = useStockData()

const impactOptions = ['All', 'High', 'Medium', 'Low'] as const
const selectedImpact = ref<(typeof impactOptions)[number]>('All')

const newsFeed = ref<NewsItem[]>([])

const events = ref<EventItem[]>([])

const topMovers = computed(() =>
  Object.values(stocks)
    .filter((stock) => stock.price > 0)
    .sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent))
    .slice(0, 6),
)

const filteredNews = computed(() => {
  if (selectedImpact.value === 'All') return newsFeed.value
  return newsFeed.value.filter((item) => item.impact === selectedImpact.value)
})

const highImpactCount = computed(
  () => newsFeed.value.filter((item) => item.impact === 'High').length,
)

function normalizeImpact(value: string): ImpactLevel {
  const normalized = value.toLowerCase()
  if (normalized === 'high') return 'High'
  if (normalized === 'medium') return 'Medium'
  return 'Low'
}

function formatNewsTime(value: string): string {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadNewsAndEvents(): Promise<void> {
  const symbols = ['FPT', 'VCB', 'HPG', 'VNM', 'MBB', 'TCB', 'VIC', 'MSN']

  const [newsResult, eventsResult] = await Promise.allSettled([
    stockBackendApi.getMarketNews(symbols, 24, false),
    stockBackendApi.getMarketEvents(symbols, 20, false),
  ])

  if (newsResult.status === 'fulfilled' && newsResult.value.data.length > 0) {
    newsFeed.value = newsResult.value.data.map((item, index) => ({
      id: item.id || `${item.symbol}-${index}`,
      source: item.source || 'vnstock',
      time: formatNewsTime(item.publish_time || item.time),
      impact: normalizeImpact(item.impact),
      title: item.title,
      summary: item.summary || item.title,
      symbols: item.symbols.length > 0 ? item.symbols : [item.symbol],
    }))
  }

  if (eventsResult.status === 'fulfilled' && eventsResult.value.data.length > 0) {
    events.value = eventsResult.value.data.map((item, index) => ({
      id: item.id || `${item.symbol}-event-${index}`,
      date: item.date || '',
      title: item.title || 'Corporate Event',
      description: item.description || 'Corporate event update.',
      symbol: item.symbol || 'VN30',
    }))
  }
}

function impactClass(impact: ImpactLevel): string {
  if (impact === 'High') return 'bg-error-50 text-error-700 dark:bg-error-500/15 dark:text-error-400'
  if (impact === 'Medium') return 'bg-warning-50 text-warning-700 dark:bg-warning-500/15 dark:text-warning-400'
  return 'bg-success-50 text-success-700 dark:bg-success-500/15 dark:text-success-400'
}

function goToStock(symbol: string): void {
  void router.push(`/stocks/${symbol}`)
}

onMounted(async () => {
  await fetchInitialData()
  await loadNewsAndEvents()

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
