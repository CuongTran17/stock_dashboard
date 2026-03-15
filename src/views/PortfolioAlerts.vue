<template>
  <AdminLayout>
    <div class="space-y-6">
      <div class="flex flex-col gap-2">
        <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">Portfolio & Alerts</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Track your positions and monitor price targets in real time.
        </p>
      </div>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
          <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Total Market Value</p>
          <p class="mt-2 text-2xl font-semibold text-gray-800 dark:text-white/90">{{ formatCurrency(summary.totalValue) }}</p>
        </div>
        <div class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
          <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Total Cost</p>
          <p class="mt-2 text-2xl font-semibold text-gray-800 dark:text-white/90">{{ formatCurrency(summary.totalCost) }}</p>
        </div>
        <div class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
          <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Unrealized PnL</p>
          <p
            class="mt-2 text-2xl font-semibold"
            :class="summary.totalPnl >= 0 ? 'text-success-600' : 'text-error-600'"
          >
            {{ summary.totalPnl >= 0 ? '+' : '' }}{{ formatCurrency(summary.totalPnl) }}
          </p>
        </div>
      </div>

      <section class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
        <h2 class="mb-4 text-lg font-semibold text-gray-800 dark:text-white/90">Positions</h2>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead>
              <tr class="border-b border-gray-200 dark:border-gray-700">
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Symbol</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Quantity</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Avg Price</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Current Price</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">Market Value</th>
                <th class="px-3 py-2 font-medium text-gray-500 dark:text-gray-400">PnL</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="position in enrichedPositions"
                :key="position.symbol"
                class="border-b border-gray-100 dark:border-gray-800"
              >
                <td class="px-3 py-2 font-medium text-gray-800 dark:text-white/90">{{ position.symbol }}</td>
                <td class="px-3 py-2 text-gray-700 dark:text-gray-300">{{ position.quantity }}</td>
                <td class="px-3 py-2 text-gray-700 dark:text-gray-300">{{ formatPrice(position.avgPrice) }}</td>
                <td class="px-3 py-2 text-gray-700 dark:text-gray-300">{{ formatPrice(position.currentPrice) }}</td>
                <td class="px-3 py-2 text-gray-700 dark:text-gray-300">{{ formatCurrency(position.marketValue) }}</td>
                <td
                  class="px-3 py-2 font-medium"
                  :class="position.pnl >= 0 ? 'text-success-600' : 'text-error-600'"
                >
                  {{ position.pnl >= 0 ? '+' : '' }}{{ formatCurrency(position.pnl) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div class="grid grid-cols-12 gap-4 md:gap-6">
        <section class="col-span-12 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] xl:col-span-7">
          <h2 class="mb-4 text-lg font-semibold text-gray-800 dark:text-white/90">Price Alerts</h2>

          <form class="grid grid-cols-1 gap-3 md:grid-cols-4" @submit.prevent="addAlert">
            <input
              v-model="newAlert.symbol"
              type="text"
              placeholder="Symbol"
              class="h-10 rounded-lg border border-gray-300 bg-transparent px-3 text-sm dark:border-gray-700"
            />
            <select
              v-model="newAlert.direction"
              class="h-10 rounded-lg border border-gray-300 bg-transparent px-3 text-sm dark:border-gray-700"
            >
              <option value="above">Above</option>
              <option value="below">Below</option>
            </select>
            <input
              v-model.number="newAlert.targetPrice"
              type="number"
              min="0"
              placeholder="Target price"
              class="h-10 rounded-lg border border-gray-300 bg-transparent px-3 text-sm dark:border-gray-700"
            />
            <button
              type="submit"
              class="h-10 rounded-lg bg-brand-500 px-3 text-sm font-medium text-white hover:bg-brand-600"
            >
              Add Alert
            </button>
          </form>

          <div class="mt-4 space-y-2">
            <div
              v-for="alert in alerts"
              :key="alert.id"
              class="flex flex-col gap-2 rounded-lg border border-gray-100 px-3 py-2 dark:border-gray-800 sm:flex-row sm:items-center sm:justify-between"
            >
              <div class="text-sm">
                <span class="font-semibold text-gray-800 dark:text-white/90">{{ alert.symbol }}</span>
                <span class="mx-1 text-gray-500 dark:text-gray-400">{{ alert.direction === 'above' ? '>' : '<' }}</span>
                <span class="text-gray-700 dark:text-gray-300">{{ formatPrice(alert.targetPrice) }}</span>
              </div>

              <div class="flex items-center gap-3">
                <span
                  class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="
                    isTriggered(alert)
                      ? 'bg-warning-50 text-warning-700 dark:bg-warning-500/15 dark:text-warning-400'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                  "
                >
                  {{ isTriggered(alert) ? 'Triggered' : 'Watching' }}
                </span>
                <button
                  class="text-xs font-medium text-error-600"
                  @click="removeAlert(alert.id)"
                >
                  Remove
                </button>
              </div>
            </div>
          </div>
        </section>

        <section class="col-span-12 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] xl:col-span-5">
          <h2 class="mb-4 text-lg font-semibold text-gray-800 dark:text-white/90">Triggered Alerts</h2>

          <div v-if="triggeredAlerts.length === 0" class="text-sm text-gray-500 dark:text-gray-400">
            No active triggers at the moment.
          </div>

          <ul v-else class="space-y-2">
            <li
              v-for="alert in triggeredAlerts"
              :key="`triggered-${alert.id}`"
              class="rounded-lg bg-warning-50 px-3 py-2 text-sm text-warning-700 dark:bg-warning-500/10 dark:text-warning-400"
            >
              {{ alert.symbol }} crossed
              {{ alert.direction === 'above' ? 'above' : 'below' }} {{ formatPrice(alert.targetPrice) }}
              (current: {{ formatPrice(currentPriceMap[alert.symbol] || 0) }})
            </li>
          </ul>
        </section>
      </div>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { useStockData } from '@/composables/useStockData'

interface PortfolioPosition {
  symbol: string
  quantity: number
  avgPrice: number
}

interface PriceAlert {
  id: number
  symbol: string
  targetPrice: number
  direction: 'above' | 'below'
}

const {
  stocks,
  fetchInitialData,
  connectRealtime,
  startPolling,
  addToWatchlist,
  cleanup,
} = useStockData()

const positions = ref<PortfolioPosition[]>([
  { symbol: 'FPT', quantity: 500, avgPrice: 120000 },
  { symbol: 'VCB', quantity: 350, avgPrice: 90500 },
  { symbol: 'HPG', quantity: 1500, avgPrice: 26100 },
  { symbol: 'MBB', quantity: 1000, avgPrice: 23500 },
])

const alerts = ref<PriceAlert[]>([
  { id: 1, symbol: 'FPT', targetPrice: 130000, direction: 'above' },
  { id: 2, symbol: 'VCB', targetPrice: 90000, direction: 'below' },
])

const newAlert = reactive({
  symbol: 'FPT',
  targetPrice: 0,
  direction: 'above' as 'above' | 'below',
})

const currentPriceMap = computed<Record<string, number>>(() => {
  const map: Record<string, number> = {}
  Object.values(stocks).forEach((stock) => {
    map[stock.symbol] = stock.price
  })
  return map
})

const enrichedPositions = computed(() =>
  positions.value.map((position) => {
    const currentPrice = currentPriceMap.value[position.symbol] || position.avgPrice
    const marketValue = currentPrice * position.quantity
    const totalCost = position.avgPrice * position.quantity

    return {
      ...position,
      currentPrice,
      marketValue,
      pnl: marketValue - totalCost,
    }
  }),
)

const summary = computed(() => {
  const totalValue = enrichedPositions.value.reduce((sum, item) => sum + item.marketValue, 0)
  const totalCost = enrichedPositions.value.reduce((sum, item) => sum + item.avgPrice * item.quantity, 0)

  return {
    totalValue,
    totalCost,
    totalPnl: totalValue - totalCost,
  }
})

const triggeredAlerts = computed(() => alerts.value.filter((alert) => isTriggered(alert)))

function isTriggered(alert: PriceAlert): boolean {
  const currentPrice = currentPriceMap.value[alert.symbol]
  if (!currentPrice) return false

  if (alert.direction === 'above') {
    return currentPrice >= alert.targetPrice
  }

  return currentPrice <= alert.targetPrice
}

function formatPrice(value: number): string {
  return new Intl.NumberFormat('vi-VN', {
    maximumFractionDigits: 0,
  }).format(value)
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(value)
}

function addAlert(): void {
  const symbol = newAlert.symbol.trim().toUpperCase()
  if (!symbol || newAlert.targetPrice <= 0) return

  const nextId = alerts.value.length > 0 ? Math.max(...alerts.value.map((item) => item.id)) + 1 : 1

  alerts.value.push({
    id: nextId,
    symbol,
    targetPrice: newAlert.targetPrice,
    direction: newAlert.direction,
  })

  addToWatchlist(symbol)
  newAlert.targetPrice = 0
}

function removeAlert(id: number): void {
  alerts.value = alerts.value.filter((alert) => alert.id !== id)
}

onMounted(async () => {
  await fetchInitialData()

  const watchSymbols = new Set<string>()
  positions.value.forEach((position) => watchSymbols.add(position.symbol))
  alerts.value.forEach((alert) => watchSymbols.add(alert.symbol))
  watchSymbols.forEach((symbol) => addToWatchlist(symbol))

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
