<template>
  <AdminLayout>
    <div class="space-y-6">
      <section class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-800 dark:text-white/90">VN30 Financial Analyzer</h1>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Phân tích cổ phiếu bằng AI với dữ liệu realtime từ backend_v2.
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <div class="inline-flex items-center gap-1 rounded-xl bg-gray-100 p-1 dark:bg-gray-800">
              <button
                class="rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors"
                :class="
                  currentView === 'dashboard'
                    ? 'bg-white text-gray-900 shadow-theme-xs dark:bg-gray-900 dark:text-white'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                "
                @click="switchView('dashboard')"
              >
                Dashboard
              </button>
              <button
                class="rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors"
                :class="
                  currentView === 'ai-analysis'
                    ? 'bg-white text-gray-900 shadow-theme-xs dark:bg-gray-900 dark:text-white'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                "
                @click="switchView('ai-analysis')"
              >
                Phân tích cổ phiếu bằng AI
              </button>
            </div>

            <span class="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
              {{ analysis.model }}
            </span>

            <span class="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
              <span class="h-2 w-2 rounded-full" :class="statusDotClass"></span>
              {{ statusLabel }}
            </span>

            <button
              class="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              @click="toggleSettings"
            >
              Cấu hình
            </button>
          </div>
        </div>

        <div class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          <div class="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-800/60">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Nguồn dữ liệu</p>
            <p class="mt-1 text-sm font-semibold text-gray-800 dark:text-white/90">FastAPI backend_v2</p>
          </div>
          <div class="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-800/60">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Pipeline</p>
            <p class="mt-1 text-sm font-semibold text-gray-800 dark:text-white/90">Technical + News + Event + Fundamentals</p>
          </div>
          <div class="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-800/60">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Mã đang theo dõi</p>
            <p class="mt-1 text-sm font-semibold text-gray-800 dark:text-white/90">{{ selectedSymbol }}</p>
          </div>
        </div>

        <div
          v-if="showSettings"
          class="mt-4 rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm dark:border-gray-700 dark:bg-gray-800/50"
        >
          <p class="font-semibold text-gray-800 dark:text-white/90">Cấu hình AI Analyzer</p>
          <p class="mt-1 text-gray-500 dark:text-gray-400">
            Trang này đã port cấu trúc từ AI-Financial-Analyzer và đồng bộ lại theo theme/layout hiện tại của dự án VN30.
          </p>
          <div class="mt-3 flex flex-wrap gap-2">
            <span class="rounded-full bg-white px-3 py-1 text-xs font-medium text-gray-700 dark:bg-gray-900 dark:text-gray-300">Model: {{ analysis.model }}</span>
            <span class="rounded-full bg-white px-3 py-1 text-xs font-medium text-gray-700 dark:bg-gray-900 dark:text-gray-300">Backend: {{ backendLabel }}</span>
            <span class="rounded-full bg-white px-3 py-1 text-xs font-medium text-gray-700 dark:bg-gray-900 dark:text-gray-300">Last update: {{ lastUpdatedLabel }}</span>
          </div>
        </div>
      </section>

      <div class="grid grid-cols-12 gap-4 md:gap-6">
        <section
          class="col-span-12 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]"
          :class="currentView === 'dashboard' ? 'xl:col-span-8' : 'xl:col-span-7'"
        >
          <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">Market View</h2>
            <div class="flex flex-wrap items-center gap-2">
              <select
                v-model="selectedSymbol"
                class="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 outline-none transition focus:border-brand-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:focus:border-brand-600"
                @change="onSymbolChange"
              >
                <option v-for="symbol in symbolOptions" :key="symbol" :value="symbol">{{ symbol }}</option>
              </select>

              <button
                class="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                :disabled="isBusy || isAnalyzing"
                @click="refreshAll(true, true)"
              >
                Refresh
              </button>

              <button
                class="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                :disabled="isBusy || isAnalyzing"
                @click="refreshAll(false, true)"
              >
                Sync Cache
              </button>
            </div>
          </div>

          <div ref="chartContainer" class="h-[420px] w-full overflow-hidden rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900"></div>

          <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/60">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Price</p>
              <p class="mt-1 text-lg font-semibold text-gray-800 dark:text-white/90">{{ currentPriceDisplay }}</p>
            </div>
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/60">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Daily Change</p>
              <p class="mt-1 text-lg font-semibold" :class="priceChangeClass">{{ currentChangeDisplay }}</p>
            </div>
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/60">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Volume</p>
              <p class="mt-1 text-lg font-semibold text-gray-800 dark:text-white/90">{{ volumeDisplay }}</p>
            </div>
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/60">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">RSI (14)</p>
              <p class="mt-1 text-lg font-semibold text-gray-800 dark:text-white/90">{{ rsiDisplay }}</p>
            </div>
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/60">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">20D Vol</p>
              <p class="mt-1 text-lg font-semibold text-gray-800 dark:text-white/90">{{ volatilityDisplay }}</p>
            </div>
          </div>
        </section>

        <section
          class="col-span-12 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]"
          :class="currentView === 'dashboard' ? 'xl:col-span-4' : 'xl:col-span-5'"
        >
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">AI Brain Explorer</h2>
            <button
              class="rounded-lg bg-brand-500 px-3 py-2 text-xs font-semibold text-white transition hover:bg-brand-600 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="isBusy || isAnalyzing"
              @click="generateAnalysis(true)"
            >
              {{ isAnalyzing ? 'Analyzing...' : 'Analyze Now' }}
            </button>
          </div>

          <div class="rounded-xl border px-4 py-5 text-center" :class="decisionBadgeClass">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Decision</p>
            <p class="mt-2 text-4xl font-bold">{{ analysis.decision }}</p>
          </div>

          <div class="mt-4 rounded-xl border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800/60">
            <div class="flex items-center justify-between text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
              <span>Confidence</span>
              <span>{{ analysis.confidence }}%</span>
            </div>
            <div class="mt-2 h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
              <div class="h-full rounded-full bg-brand-500 transition-all" :style="{ width: `${analysis.confidence}%` }"></div>
            </div>
          </div>

          <div class="mt-4 inline-flex w-full flex-wrap items-center gap-1 rounded-xl bg-gray-100 p-1 dark:bg-gray-800">
            <button
              v-for="tab in tabList"
              :key="tab.key"
              class="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold transition-colors"
              :class="
                activeTab === tab.key
                  ? 'bg-white text-gray-900 shadow-theme-xs dark:bg-gray-900 dark:text-white'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              "
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
              <span v-if="hasTabContent(tab.key)" class="h-1.5 w-1.5 rounded-full bg-success-500"></span>
            </button>
          </div>

          <div class="mt-3 rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800/60">
            <div v-show="activeTab === 'full'">
              <p class="mb-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Full Analysis</p>
              <div class="max-h-52 overflow-y-auto text-sm leading-6 text-gray-600 dark:text-gray-300" v-html="tabContent.full"></div>
            </div>
            <div v-show="activeTab === 'technical'">
              <p class="mb-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Technical</p>
              <div class="max-h-52 overflow-y-auto text-sm leading-6 text-gray-600 dark:text-gray-300" v-html="tabContent.technical"></div>
            </div>
            <div v-show="activeTab === 'fundamental'">
              <p class="mb-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Fundamental</p>
              <div class="max-h-52 overflow-y-auto text-sm leading-6 text-gray-600 dark:text-gray-300" v-html="tabContent.fundamental"></div>
            </div>
            <div v-show="activeTab === 'sentiment'">
              <p class="mb-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Sentiment</p>
              <div class="max-h-52 overflow-y-auto text-sm leading-6 text-gray-600 dark:text-gray-300" v-html="tabContent.sentiment"></div>
            </div>
            <div v-show="activeTab === 'conclusion'">
              <p class="mb-2 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Conclusion</p>
              <div class="max-h-52 overflow-y-auto text-sm leading-6 text-gray-600 dark:text-gray-300" v-html="tabContent.conclusion"></div>
            </div>
          </div>

          <div class="mt-3 rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800/60">
            <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Key Factors</p>
            <ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-gray-600 dark:text-gray-300">
              <li v-for="factor in analysis.factors" :key="factor">{{ factor }}</li>
              <li v-if="analysis.factors.length === 0" class="italic text-gray-500 dark:text-gray-400">No factors available yet.</li>
            </ul>
          </div>
        </section>

        <section
          v-if="currentView === 'dashboard'"
          class="col-span-12 rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]"
        >
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">Backtest Tracker</h2>
            <button
              class="rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              :disabled="isBusy || isAnalyzing"
              @click="rebuildBacktest"
            >
              Recalculate
            </button>
          </div>

          <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center dark:border-gray-700 dark:bg-gray-800/60">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Total Predictions</p>
              <p class="mt-1 text-xl font-semibold text-gray-800 dark:text-white/90">{{ totalPredictions }}</p>
            </div>
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center dark:border-gray-700 dark:bg-gray-800/60">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Win Rate</p>
              <p class="mt-1 text-xl font-semibold text-gray-800 dark:text-white/90">{{ winRateDisplay }}</p>
            </div>
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center dark:border-gray-700 dark:bg-gray-800/60">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Avg Confidence</p>
              <p class="mt-1 text-xl font-semibold text-gray-800 dark:text-white/90">{{ avgConfidenceDisplay }}</p>
            </div>
            <div class="rounded-xl border border-gray-200 bg-gray-50 p-3 text-center dark:border-gray-700 dark:bg-gray-800/60">
              <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Accuracy</p>
              <p class="mt-1 text-xl font-semibold text-gray-800 dark:text-white/90">{{ accuracyDisplay }}</p>
            </div>
          </div>

          <div class="mt-4 rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800/60">
            <p class="mb-3 text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Signal Distribution</p>
            <p v-if="signalDistribution.length === 0" class="text-sm italic text-gray-500 dark:text-gray-400">
              Signal distribution will appear here...
            </p>
            <div v-else class="space-y-2">
              <div v-for="row in signalDistribution" :key="row.label" class="grid grid-cols-[100px,1fr,40px] items-center gap-3">
                <span class="text-xs font-medium text-gray-600 dark:text-gray-300">{{ row.label }}</span>
                <div class="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                  <div
                    class="h-full rounded-full transition-all"
                    :class="signalFillClass(row.className)"
                    :style="{ width: `${row.percentage.toFixed(1)}%` }"
                  ></div>
                </div>
                <span class="text-right text-xs font-medium text-gray-600 dark:text-gray-300">{{ row.percentage.toFixed(0) }}%</span>
              </div>
            </div>
          </div>

          <div class="mt-4 overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
            <table class="min-w-full text-sm">
              <thead class="bg-gray-50 dark:bg-gray-800/60">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Date</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Model</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Decision</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Confidence</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">5D Return</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">10D Return</th>
                  <th class="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="backtestRecords.length === 0">
                  <td colspan="7" class="px-3 py-6 text-center text-sm italic text-gray-500 dark:text-gray-400">No prediction history available</td>
                </tr>
                <tr
                  v-for="record in backtestRecords"
                  v-else
                  :key="`${record.date}-${record.decision}-${record.confidence}`"
                  class="border-t border-gray-200 dark:border-gray-700"
                >
                  <td class="px-3 py-2 text-gray-600 dark:text-gray-300">{{ formatDateShort(record.date) }}</td>
                  <td class="px-3 py-2 text-gray-600 dark:text-gray-300">{{ record.model }}</td>
                  <td class="px-3 py-2">
                    <span class="inline-flex rounded-md px-2 py-1 text-xs font-semibold" :class="decisionTagClass(record.decision)">
                      {{ record.decision }}
                    </span>
                  </td>
                  <td class="px-3 py-2 text-gray-600 dark:text-gray-300">{{ record.confidence }}%</td>
                  <td class="px-3 py-2 text-gray-600 dark:text-gray-300">{{ formatBacktestPercent(record.return5d) }}</td>
                  <td class="px-3 py-2 text-gray-600 dark:text-gray-300">{{ formatBacktestPercent(record.return10d) }}</td>
                  <td class="px-3 py-2 text-gray-600 dark:text-gray-300">{{ backtestStatusLabel(record) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <div
        v-if="isBusy || isAnalyzing"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-gray-900/35 backdrop-blur-[2px] dark:bg-gray-900/55"
      >
        <div class="rounded-xl border border-gray-200 bg-white px-6 py-5 text-center shadow-theme-xl dark:border-gray-700 dark:bg-gray-800">
          <div class="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-500 dark:border-brand-900/30 dark:border-t-brand-400"></div>
          <p class="mt-3 text-sm font-medium text-gray-700 dark:text-gray-200">{{ loadingMessage }}</p>
        </div>
      </div>

      <div
        v-if="alertVisible"
        class="fixed right-6 top-24 z-[9999] rounded-lg border px-4 py-2 text-sm font-medium shadow-theme-md"
        :class="{
          'border-success-300 bg-success-50 text-success-700 dark:border-success-700 dark:bg-success-500/15 dark:text-success-300': alertType === 'success',
          'border-error-300 bg-error-50 text-error-700 dark:border-error-700 dark:bg-error-500/15 dark:text-error-300': alertType === 'error',
          'border-brand-300 bg-brand-50 text-brand-700 dark:border-brand-700 dark:bg-brand-500/15 dark:text-brand-300': alertType === 'info',
        }"
      >
        {{ alertMessage }}
      </div>
    </div>
  </AdminLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  CandlestickSeries,
  ColorType,
  createChart,
  type CandlestickData,
  type IChartApi,
  type ISeriesApi,
  type Time,
  type UTCTimestamp,
} from 'lightweight-charts'
import AdminLayout from '@/components/layout/AdminLayout.vue'
import { VN30_TICKERS } from '@/composables/useStockData'
import {
  stockBackendApi,
  type HistoricalRecord,
  type MarketEventItem,
  type MarketNewsItem,
  type StockSnapshot,
  type TechnicalResponse,
} from '@/services/stockBackendApi'

type ViewMode = 'dashboard' | 'ai-analysis'
type AnalysisTab = 'full' | 'technical' | 'fundamental' | 'sentiment' | 'conclusion'
type Decision = 'Strong Buy' | 'Buy' | 'Hold' | 'Sell' | 'Strong Sell'
type AppStatus = 'connected' | 'disconnected' | 'analyzing'
type AlertType = 'success' | 'error' | 'info'

interface GeneratedAnalysis {
  decision: Decision
  confidence: number
  model: string
  full: string
  technical: string
  fundamental: string
  sentiment: string
  conclusion: string
  factors: string[]
  updatedAt: string
}

interface BacktestRecord {
  date: string
  model: string
  decision: Decision
  confidence: number
  return5d: number | null
  return10d: number | null
  accurate: boolean | null
}

interface SignalDistributionRow {
  label: Decision
  className: string
  percentage: number
}

const symbolOptions = [...VN30_TICKERS]
const tabList: Array<{ key: AnalysisTab; label: string }> = [
  { key: 'full', label: 'Full' },
  { key: 'technical', label: 'Technical' },
  { key: 'fundamental', label: 'Fundamental' },
  { key: 'sentiment', label: 'Sentiment' },
  { key: 'conclusion', label: 'Conclusion' },
]

const BACKEND_FALLBACK = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
const POSITIVE_TOKENS = [
  'tang',
  'tich cuc',
  'vuot ke hoach',
  'mua',
  'breakout',
  'mo rong',
  'ky luc',
  'lai',
  'profit',
  'growth',
  'upgrade',
  'dividend',
  'co tuc',
]
const NEGATIVE_TOKENS = [
  'giam',
  'rui ro',
  'ban',
  'ap luc',
  'thua lo',
  'dieu tra',
  'downgrade',
  'warning',
  'sell',
  'bearish',
  'suy yeu',
  'volatility spike',
]
const DECISION_ORDER: Decision[] = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']

const currentView = ref<ViewMode>('dashboard')
const activeTab = ref<AnalysisTab>('full')
const selectedSymbol = ref(symbolOptions.includes('FPT') ? 'FPT' : symbolOptions[0] || 'VN30')
const status = ref<AppStatus>('connected')
const showSettings = ref(false)
const isBusy = ref(false)
const isAnalyzing = ref(false)
const isDarkTheme = ref(document.documentElement.classList.contains('dark'))
const loadingMessage = ref('Đang tải dữ liệu thị trường...')

const snapshot = ref<StockSnapshot | null>(null)
const history = ref<HistoricalRecord[]>([])
const technical = ref<TechnicalResponse | null>(null)
const newsItems = ref<MarketNewsItem[]>([])
const eventItems = ref<MarketEventItem[]>([])
const overview = ref<Record<string, unknown> | null>(null)
const backtestRecords = ref<BacktestRecord[]>([])

const analysis = ref<GeneratedAnalysis>(createEmptyAnalysis())

const alertVisible = ref(false)
const alertMessage = ref('')
const alertType = ref<AlertType>('info')
let alertTimer: ReturnType<typeof setTimeout> | null = null

const chartContainer = ref<HTMLElement | null>(null)
let chart: IChartApi | null = null
let candleSeries: ISeriesApi<'Candlestick', Time> | null = null
let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null

const numberFormatter = new Intl.NumberFormat('vi-VN', {
  maximumFractionDigits: 2,
})

const integerFormatter = new Intl.NumberFormat('vi-VN', {
  maximumFractionDigits: 0,
})

const sortedHistory = computed(() =>
  [...history.value].sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()),
)

const closeSeries = computed(() =>
  sortedHistory.value
    .map((item) => toNumber(item.close))
    .filter((value): value is number => Number.isFinite(value) && value > 0),
)

const currentPrice = computed<number | null>(() => {
  const fromSnapshot = snapshot.value ? toNumber(snapshot.value.price) : Number.NaN
  if (Number.isFinite(fromSnapshot) && fromSnapshot > 0) {
    return fromSnapshot
  }

  const closes = closeSeries.value
  return closes.length > 0 ? closes[closes.length - 1] : null
})

const previousClose = computed<number | null>(() => {
  const closes = closeSeries.value
  return closes.length > 1 ? closes[closes.length - 2] : null
})

const currentChangePercent = computed<number | null>(() => {
  const fromSnapshot = snapshot.value ? toNumber(snapshot.value.changePercent) : Number.NaN
  if (Number.isFinite(fromSnapshot)) {
    return fromSnapshot
  }

  if (currentPrice.value !== null && previousClose.value !== null && previousClose.value > 0) {
    return ((currentPrice.value - previousClose.value) / previousClose.value) * 100
  }

  return null
})

const currentVolume = computed<number | null>(() => {
  const fromSnapshot = snapshot.value ? toNumber(snapshot.value.volume) : Number.NaN
  if (Number.isFinite(fromSnapshot) && fromSnapshot >= 0) {
    return fromSnapshot
  }

  const latest = sortedHistory.value[sortedHistory.value.length - 1]
  if (!latest) {
    return null
  }

  const parsed = toNumber(latest.volume)
  return Number.isFinite(parsed) ? parsed : null
})

const currentRsi = computed<number | null>(() => {
  const fromTechnical = latestNumber(technical.value?.indicators.rsi_14 || [])
  if (fromTechnical !== null) {
    return fromTechnical
  }

  return latestNumber(computeRsiSeries(closeSeries.value))
})

const currentVolatility = computed<number | null>(() => {
  const closes = closeSeries.value
  if (closes.length < 4) {
    return null
  }

  return computeAnnualizedVolatility(closes.slice(-21))
})

const currentPriceDisplay = computed(() => formatPrice(currentPrice.value))
const currentChangeDisplay = computed(() => formatPercent(currentChangePercent.value))
const volumeDisplay = computed(() => formatVolume(currentVolume.value))
const rsiDisplay = computed(() => (currentRsi.value === null ? 'N/A' : currentRsi.value.toFixed(2)))
const volatilityDisplay = computed(() =>
  currentVolatility.value === null ? 'N/A' : `${currentVolatility.value.toFixed(2)}%`,
)

const priceChangeClass = computed(() => {
  const value = currentChangePercent.value
  if (value === null || !Number.isFinite(value)) {
    return 'text-gray-800 dark:text-white/90'
  }
  return value >= 0
    ? 'text-success-600 dark:text-success-400'
    : 'text-error-600 dark:text-error-400'
})

const statusDotClass = computed(() => {
  if (status.value === 'connected') return 'bg-success-500'
  if (status.value === 'analyzing') return 'bg-warning-500 animate-pulse'
  return 'bg-error-500'
})

const statusLabel = computed(() => {
  if (status.value === 'connected') return 'Online'
  if (status.value === 'analyzing') return 'Analyzing...'
  return 'Offline'
})

const decisionBadgeClass = computed(() => {
  switch (analysis.value.decision) {
    case 'Strong Buy':
    case 'Buy':
      return 'border-success-200 bg-success-50 text-success-700 dark:border-success-700 dark:bg-success-500/15 dark:text-success-300'
    case 'Hold':
      return 'border-warning-200 bg-warning-50 text-warning-700 dark:border-warning-700 dark:bg-warning-500/15 dark:text-warning-300'
    case 'Sell':
    case 'Strong Sell':
      return 'border-error-200 bg-error-50 text-error-700 dark:border-error-700 dark:bg-error-500/15 dark:text-error-300'
    default:
      return 'border-gray-200 bg-gray-50 text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300'
  }
})

const backendLabel = computed(() => BACKEND_FALLBACK)
const lastUpdatedLabel = computed(() => formatDateTime(analysis.value.updatedAt))

const totalPredictions = computed(() => backtestRecords.value.length)

const completedPredictions = computed(() =>
  backtestRecords.value.filter((item) => item.accurate !== null),
)

const correctPredictions = computed(
  () => completedPredictions.value.filter((item) => item.accurate === true).length,
)

const winRate = computed(() => {
  const completed = completedPredictions.value.length
  if (completed === 0) {
    return 0
  }
  return (correctPredictions.value / completed) * 100
})

const avgConfidence = computed(() => {
  if (backtestRecords.value.length === 0) {
    return 0
  }

  const total = backtestRecords.value.reduce((sum, item) => sum + item.confidence, 0)
  return total / backtestRecords.value.length
})

const winRateDisplay = computed(() => `${winRate.value.toFixed(1)}%`)
const avgConfidenceDisplay = computed(() => `${avgConfidence.value.toFixed(1)}%`)
const accuracyDisplay = computed(() => `${winRate.value.toFixed(1)}%`)

const signalDistribution = computed<SignalDistributionRow[]>(() => {
  if (backtestRecords.value.length === 0) {
    return []
  }

  const counts = DECISION_ORDER.reduce<Record<Decision, number>>((acc, decision) => {
    acc[decision] = 0
    return acc
  }, {
    'Strong Buy': 0,
    Buy: 0,
    Hold: 0,
    Sell: 0,
    'Strong Sell': 0,
  })

  backtestRecords.value.forEach((record) => {
    counts[record.decision] += 1
  })

  const total = backtestRecords.value.length

  return DECISION_ORDER.map((decision) => ({
    label: decision,
    className: toDecisionClass(decision),
    percentage: total > 0 ? (counts[decision] / total) * 100 : 0,
  }))
})

const TAB_TO_FIELD: Record<AnalysisTab, keyof Pick<GeneratedAnalysis, 'full' | 'technical' | 'fundamental' | 'sentiment' | 'conclusion'>> = {
  full: 'full',
  technical: 'technical',
  fundamental: 'fundamental',
  sentiment: 'sentiment',
  conclusion: 'conclusion',
}

const tabContent = computed(() => ({
  full: toHtmlBlock(analysis.value.full, 'No full analysis available.'),
  technical: toHtmlBlock(analysis.value.technical, 'No technical analysis available.'),
  fundamental: toHtmlBlock(analysis.value.fundamental, 'No fundamental analysis available.'),
  sentiment: toHtmlBlock(analysis.value.sentiment, 'No sentiment analysis available.'),
  conclusion: toHtmlBlock(analysis.value.conclusion, 'No conclusion available.'),
}))

function createEmptyAnalysis(): GeneratedAnalysis {
  return {
    decision: 'Hold',
    confidence: 0,
    model: 'VN30 Analyst AI',
    full: '',
    technical: '',
    fundamental: '',
    sentiment: '',
    conclusion: '',
    factors: [],
    updatedAt: new Date(0).toISOString(),
  }
}

function toNumber(value: unknown, fallback: number = Number.NaN): number {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : fallback
  }

  if (typeof value === 'string') {
    const parsed = Number(value.replace(/,/g, ''))
    return Number.isFinite(parsed) ? parsed : fallback
  }

  return fallback
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function latestNumber(values: Array<number | null | undefined>): number | null {
  for (let index = values.length - 1; index >= 0; index -= 1) {
    const value = values[index]
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value
    }
  }
  return null
}

function formatPrice(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return 'N/A'
  }
  return numberFormatter.format(value)
}

function formatPercent(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return 'N/A'
  }
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function formatVolume(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return 'N/A'
  }

  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`
  return integerFormatter.format(value)
}

function formatDateTime(value: string): string {
  if (!value) {
    return '--'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDateShort(value: string): string {
  if (!value) {
    return '--'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })
}

function formatBacktestPercent(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return 'N/A'
  }
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function toHtmlBlock(text: string, fallback: string): string {
  const content = text.trim()
  if (!content) {
    return `<p><em>${escapeHtml(fallback)}</em></p>`
  }

  return `<p>${escapeHtml(content).replace(/\n/g, '<br>')}</p>`
}

function normalizeText(input: string): string {
  return input
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
}

function scoreSentimentText(rawText: string): number {
  const text = normalizeText(rawText)

  let positiveHits = 0
  let negativeHits = 0

  POSITIVE_TOKENS.forEach((token) => {
    if (text.includes(token)) {
      positiveHits += 1
    }
  })

  NEGATIVE_TOKENS.forEach((token) => {
    if (text.includes(token)) {
      negativeHits += 1
    }
  })

  return positiveHits - negativeHits
}

function computeAnnualizedVolatility(closes: number[]): number | null {
  if (closes.length < 3) {
    return null
  }

  const logReturns: number[] = []
  for (let index = 1; index < closes.length; index += 1) {
    const previous = closes[index - 1]
    const current = closes[index]
    if (previous > 0 && current > 0) {
      logReturns.push(Math.log(current / previous))
    }
  }

  if (logReturns.length < 2) {
    return null
  }

  const mean = logReturns.reduce((sum, value) => sum + value, 0) / logReturns.length
  const variance =
    logReturns.reduce((sum, value) => sum + (value - mean) ** 2, 0) / logReturns.length

  return Math.sqrt(variance) * Math.sqrt(252) * 100
}

function computeSmaSeries(closes: number[], period: number): Array<number | null> {
  const output: Array<number | null> = Array(closes.length).fill(null)
  if (closes.length < period) {
    return output
  }

  let rollingSum = 0
  for (let index = 0; index < closes.length; index += 1) {
    rollingSum += closes[index]

    if (index >= period) {
      rollingSum -= closes[index - period]
    }

    if (index >= period - 1) {
      output[index] = rollingSum / period
    }
  }

  return output
}

function computeRsiSeries(closes: number[], period: number = 14): Array<number | null> {
  const output: Array<number | null> = Array(closes.length).fill(null)
  if (closes.length <= period) {
    return output
  }

  let gainSum = 0
  let lossSum = 0

  for (let index = 1; index <= period; index += 1) {
    const delta = closes[index] - closes[index - 1]
    gainSum += Math.max(delta, 0)
    lossSum += Math.max(-delta, 0)
  }

  let avgGain = gainSum / period
  let avgLoss = lossSum / period

  output[period] = computeRsiValue(avgGain, avgLoss)

  for (let index = period + 1; index < closes.length; index += 1) {
    const delta = closes[index] - closes[index - 1]
    const gain = Math.max(delta, 0)
    const loss = Math.max(-delta, 0)

    avgGain = (avgGain * (period - 1) + gain) / period
    avgLoss = (avgLoss * (period - 1) + loss) / period

    output[index] = computeRsiValue(avgGain, avgLoss)
  }

  return output
}

function computeRsiValue(avgGain: number, avgLoss: number): number {
  if (avgLoss === 0 && avgGain === 0) {
    return 50
  }
  if (avgLoss === 0) {
    return 100
  }

  const rs = avgGain / avgLoss
  return 100 - 100 / (1 + rs)
}

function signalSummaryLabel(summary: TechnicalResponse['signals']['summary'] | 'neutral'): string {
  if (summary === 'strong_buy') return 'Strong Buy'
  if (summary === 'buy') return 'Buy'
  if (summary === 'sell') return 'Sell'
  if (summary === 'strong_sell') return 'Strong Sell'
  return 'Neutral'
}

function scoreToDecision(score: number): Decision {
  if (score >= 4.5) return 'Strong Buy'
  if (score >= 1.8) return 'Buy'
  if (score > -1.8) return 'Hold'
  if (score > -4.5) return 'Sell'
  return 'Strong Sell'
}

function toDecisionClass(decision: Decision): string {
  return decision.toLowerCase().replace(/\s+/g, '-')
}

function signalFillClass(decisionClass: string): string {
  if (decisionClass === 'hold') {
    return 'bg-warning-500'
  }

  if (decisionClass === 'sell' || decisionClass === 'strong-sell') {
    return 'bg-error-500'
  }

  return 'bg-success-500'
}

function decisionTagClass(decision: Decision): string {
  switch (decision) {
    case 'Strong Buy':
    case 'Buy':
      return 'bg-success-50 text-success-700 dark:bg-success-500/15 dark:text-success-300'
    case 'Hold':
      return 'bg-warning-50 text-warning-700 dark:bg-warning-500/15 dark:text-warning-300'
    case 'Sell':
    case 'Strong Sell':
      return 'bg-error-50 text-error-700 dark:bg-error-500/15 dark:text-error-300'
    default:
      return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
  }
}

function backtestStatusLabel(record: BacktestRecord): string {
  if (record.accurate === null) return 'Pending'
  return record.accurate ? 'Correct' : 'Incorrect'
}

function evaluatePrediction(decision: Decision, return5d: number | null): boolean | null {
  if (return5d === null || !Number.isFinite(return5d)) {
    return null
  }

  if (decision === 'Strong Buy' || decision === 'Buy') {
    return return5d > 0
  }

  if (decision === 'Strong Sell' || decision === 'Sell') {
    return return5d < 0
  }

  return Math.abs(return5d) <= 2
}

function extractOverviewMetric(keywords: string[]): number | null {
  if (!overview.value) {
    return null
  }

  const lowered = keywords.map((keyword) => keyword.toLowerCase())

  const walk = (node: unknown): number | null => {
    if (!node || typeof node !== 'object') {
      return null
    }

    for (const [key, value] of Object.entries(node as Record<string, unknown>)) {
      const normalizedKey = key.toLowerCase()

      if (lowered.some((keyword) => normalizedKey.includes(keyword))) {
        const parsed = toNumber(value)
        if (Number.isFinite(parsed)) {
          return parsed
        }
      }

      if (value && typeof value === 'object') {
        const nested = walk(value)
        if (nested !== null) {
          return nested
        }
      }
    }

    return null
  }

  return walk(overview.value)
}

function buildAnalysis(): GeneratedAnalysis {
  const technicalData = technical.value
  const closes = closeSeries.value
  const latestClose = closes.length > 0 ? closes[closes.length - 1] : null

  let score = 0
  const factorPool: string[] = []

  const rsiValue = latestNumber(technicalData?.indicators.rsi_14 || []) || latestNumber(computeRsiSeries(closes))
  if (rsiValue !== null) {
    if (rsiValue < 30) {
      score += 2.2
      factorPool.push(`RSI ${rsiValue.toFixed(2)} cho thấy vùng quá bán.`)
    } else if (rsiValue > 70) {
      score -= 2.2
      factorPool.push(`RSI ${rsiValue.toFixed(2)} cho thấy vùng quá mua.`)
    } else if (rsiValue >= 45 && rsiValue <= 60) {
      score += 0.6
      factorPool.push(`RSI ${rsiValue.toFixed(2)} đang ở vùng cân bằng tích cực.`)
    }
  }

  const macdSignal = technicalData?.signals.macd
  if (macdSignal === 'bullish') {
    score += 1.2
    factorPool.push('MACD đang ở trạng thái bullish.')
  } else if (macdSignal === 'bearish') {
    score -= 1.2
    factorPool.push('MACD đang ở trạng thái bearish.')
  }

  const summarySignal = technicalData?.signals.summary || 'neutral'
  const summaryWeight: Record<TechnicalResponse['signals']['summary'] | 'neutral', number> = {
    strong_buy: 3,
    buy: 1.6,
    neutral: 0,
    sell: -1.6,
    strong_sell: -3,
  }
  score += summaryWeight[summarySignal]
  factorPool.push(`Tín hiệu kỹ thuật tổng hợp: ${signalSummaryLabel(summarySignal)}.`)

  const sma20 = latestNumber(technicalData?.indicators.sma_20 || computeSmaSeries(closes, 20))
  if (latestClose !== null && sma20 !== null && sma20 > 0) {
    if (latestClose >= sma20) {
      score += 1
      factorPool.push('Giá hiện tại đang cao hơn SMA20.')
    } else {
      score -= 1
      factorPool.push('Giá hiện tại đang thấp hơn SMA20.')
    }
  }

  if (closes.length > 6) {
    const previous5 = closes[closes.length - 6]
    const momentum5d = previous5 > 0 ? ((closes[closes.length - 1] - previous5) / previous5) * 100 : 0

    if (momentum5d >= 2) {
      score += 0.9
      factorPool.push(`Động lượng 5 phiên: +${momentum5d.toFixed(2)}%.`)
    } else if (momentum5d <= -2) {
      score -= 0.9
      factorPool.push(`Động lượng 5 phiên: ${momentum5d.toFixed(2)}%.`)
    }
  }

  const sentimentRaw = newsItems.value
    .slice(0, 12)
    .reduce((sum, item) => sum + scoreSentimentText(`${item.title} ${item.summary}`), 0)
  const sentimentScore = clamp(sentimentRaw / 3, -2, 2)
  if (sentimentScore !== 0) {
    score += sentimentScore
    factorPool.push(`Sentiment tin tức đóng góp ${sentimentScore > 0 ? '+' : ''}${sentimentScore.toFixed(2)} điểm.`)
  } else if (newsItems.value.length === 0) {
    factorPool.push('Không có nhiều tin tức mới cho mã đang chọn.')
  }

  const hasPositiveEvent = eventItems.value.some((item) =>
    /co tuc|dividend|thuong|mua lai/.test(normalizeText(`${item.title} ${item.description}`)),
  )
  const hasRiskEvent = eventItems.value.some((item) =>
    /dieu tra|phat|canh bao|tranh chap|lo/.test(normalizeText(`${item.title} ${item.description}`)),
  )

  if (hasPositiveEvent) {
    score += 0.5
    factorPool.push('Có tín hiệu sự kiện doanh nghiệp tích cực.')
  }

  if (hasRiskEvent) {
    score -= 0.8
    factorPool.push('Có sự kiện cần theo dõi rủi ro trong ngắn hạn.')
  }

  const pe = extractOverviewMetric(['pe', 'p/e', 'price_earning'])
  if (pe !== null && pe > 0) {
    if (pe < 15) {
      score += 0.7
      factorPool.push(`P/E ở mức ${pe.toFixed(2)} tương đối hấp dẫn.`)
    } else if (pe > 25) {
      score -= 0.7
      factorPool.push(`P/E ở mức ${pe.toFixed(2)} tương đối cao.`)
    }
  }

  const roe = extractOverviewMetric(['roe'])
  if (roe !== null) {
    if (roe >= 15) {
      score += 0.8
      factorPool.push(`ROE ${roe.toFixed(2)}% hỗ trợ định giá tích cực.`)
    } else if (roe < 8) {
      score -= 0.8
      factorPool.push(`ROE ${roe.toFixed(2)}% còn thấp.`)
    }
  }

  const debtEquity = extractOverviewMetric(['debt', 'de_ratio', 'debt_equity', 'no'])
  if (debtEquity !== null && debtEquity > 2) {
    score -= 0.6
    factorPool.push('Đòn bẩy tài chính đang ở mức cao.')
  }

  const coverage = [
    technicalData ? 1 : 0,
    newsItems.value.length > 0 ? 1 : 0,
    eventItems.value.length > 0 ? 1 : 0,
    overview.value ? 1 : 0,
    closes.length >= 80 ? 1 : 0,
  ].reduce((sum, value) => sum + value, 0)

  const decision = scoreToDecision(score)
  const confidence = clamp(Math.round(44 + Math.abs(score) * 9 + coverage * 6), 35, 95)

  const technicalLines: string[] = [
    `Tín hiệu tổng hợp backend: ${signalSummaryLabel(summarySignal)}.`,
    rsiValue !== null
      ? `RSI(14): ${rsiValue.toFixed(2)}.`
      : 'RSI chưa sẵn sàng do thiếu dữ liệu lịch sử.',
    macdSignal
      ? `MACD: ${macdSignal}.`
      : 'MACD chưa đủ dữ liệu cho mã đang chọn.',
    sma20 !== null && latestClose !== null
      ? `Giá so với SMA20: ${latestClose >= sma20 ? 'trên SMA20' : 'dưới SMA20'}.`
      : 'Chưa xác định được xu hướng so với SMA20.',
  ]

  const fundamentalLines: string[] = []
  if (pe !== null) {
    fundamentalLines.push(`P/E: ${pe.toFixed(2)}.`)
  }
  if (roe !== null) {
    fundamentalLines.push(`ROE: ${roe.toFixed(2)}%.`)
  }
  if (debtEquity !== null) {
    fundamentalLines.push(`Debt metric: ${debtEquity.toFixed(2)}.`)
  }
  if (fundamentalLines.length === 0) {
    fundamentalLines.push('Dữ liệu fundamentals còn hạn chế từ nguồn hiện tại.')
  }

  const sentimentLines: string[] = []
  if (newsItems.value.length > 0) {
    sentimentLines.push(`Điểm sentiment tin tức: ${sentimentScore.toFixed(2)}.`)
    newsItems.value.slice(0, 3).forEach((item, index) => {
      sentimentLines.push(`${index + 1}. ${item.title}`)
    })
  } else {
    sentimentLines.push('Không có tin tức mới đủ mạnh để tạo sentiment rõ rệt.')
  }

  if (eventItems.value.length > 0) {
    sentimentLines.push(`Số sự kiện gần đây: ${eventItems.value.length}.`)
  }

  const conclusionLines = [
    `Quyết định: ${decision}.`,
    `Độ tin cậy: ${confidence}%.`,
    `Điểm tổng hợp AI: ${score.toFixed(2)}.`,
    'Khuyến nghị quản trị rủi ro: luôn đặt ngưỡng cắt lỗ và theo dõi thanh khoản thị trường.',
  ]

  const full = [
    `Decision: ${decision} | Confidence: ${confidence}% | Score: ${score.toFixed(2)}.`,
    '',
    'Technical:',
    ...technicalLines.map((line) => `- ${line}`),
    '',
    'Fundamentals:',
    ...fundamentalLines.map((line) => `- ${line}`),
    '',
    'News & Sentiment:',
    ...sentimentLines.map((line) => `- ${line}`),
    '',
    'Conclusion:',
    ...conclusionLines.map((line) => `- ${line}`),
  ].join('\n')

  return {
    decision,
    confidence,
    model: 'VN30 Analyst AI (rule-based)',
    full,
    technical: technicalLines.join('\n'),
    fundamental: fundamentalLines.join('\n'),
    sentiment: sentimentLines.join('\n'),
    conclusion: conclusionLines.join('\n'),
    factors: [...new Set(factorPool)].slice(0, 6),
    updatedAt: new Date().toISOString(),
  }
}

function buildBacktestRecords(): BacktestRecord[] {
  const rows = sortedHistory.value
  const parsedRows = rows
    .map((row) => ({
      date: row.time,
      close: toNumber(row.close),
    }))
    .filter((row): row is { date: string; close: number } => Number.isFinite(row.close) && row.close > 0)

  if (parsedRows.length < 45) {
    return []
  }

  const closes = parsedRows.map((row) => row.close)
  const rsiSeries = computeRsiSeries(closes)
  const sma20Series = computeSmaSeries(closes, 20)
  const records: BacktestRecord[] = []

  for (let index = 25; index < parsedRows.length - 10; index += 2) {
    const currentClose = closes[index]
    const previous5 = closes[index - 5]
    const momentum = previous5 > 0 ? ((currentClose - previous5) / previous5) * 100 : 0

    let score = 0

    const rsi = rsiSeries[index]
    if (typeof rsi === 'number') {
      if (rsi < 30) score += 1.4
      else if (rsi > 70) score -= 1.4
    }

    const sma20 = sma20Series[index]
    if (typeof sma20 === 'number') {
      score += currentClose >= sma20 ? 1 : -1
    }

    if (momentum >= 2) score += 1
    if (momentum <= -2) score -= 1

    const decision = scoreToDecision(score)

    const return5d = ((closes[index + 5] - currentClose) / currentClose) * 100
    const return10d = ((closes[index + 10] - currentClose) / currentClose) * 100
    const confidence = clamp(Math.round(42 + Math.abs(score) * 12 + Math.min(20, Math.abs(momentum) * 2)), 35, 94)

    records.push({
      date: parsedRows[index].date,
      model: 'VN30 Analyst AI',
      decision,
      confidence,
      return5d,
      return10d,
      accurate: evaluatePrediction(decision, return5d),
    })
  }

  return records.slice(-24).reverse()
}

function hasTabContent(tab: AnalysisTab): boolean {
  const key = TAB_TO_FIELD[tab]
  return analysis.value[key].trim().length > 0
}

function switchView(view: ViewMode): void {
  currentView.value = view
}

function toggleSettings(): void {
  showSettings.value = !showSettings.value
}

function showAlert(message: string, type: AlertType = 'info'): void {
  alertMessage.value = message
  alertType.value = type
  alertVisible.value = true

  if (alertTimer) {
    clearTimeout(alertTimer)
  }

  alertTimer = setTimeout(() => {
    alertVisible.value = false
  }, 4000)
}

function toTimestamp(value: string): UTCTimestamp | null {
  const parsed = Date.parse(value)
  if (Number.isNaN(parsed)) {
    return null
  }
  return Math.floor(parsed / 1000) as UTCTimestamp
}

function applyChartTheme(): void {
  if (!chart) {
    return
  }

  const dark = isDarkTheme.value

  chart.applyOptions({
    layout: {
      textColor: dark ? '#cbd5e1' : '#334155',
      background: {
        type: ColorType.Solid,
        color: dark ? '#0f172a' : '#ffffff',
      },
    },
    grid: {
      vertLines: {
        color: dark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.22)',
      },
      horzLines: {
        color: dark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.22)',
      },
    },
    rightPriceScale: {
      borderColor: dark ? 'rgba(148,163,184,0.35)' : 'rgba(148,163,184,0.5)',
    },
    timeScale: {
      borderColor: dark ? 'rgba(148,163,184,0.35)' : 'rgba(148,163,184,0.5)',
      timeVisible: true,
      secondsVisible: false,
    },
  })
}

function ensureChart(): void {
  const host = chartContainer.value
  if (!host) {
    return
  }

  if (chart) {
    applyChartTheme()
    return
  }

  const dark = isDarkTheme.value

  chart = createChart(host, {
    width: host.clientWidth,
    height: host.clientHeight || 420,
    layout: {
      textColor: dark ? '#cbd5e1' : '#334155',
      background: {
        type: ColorType.Solid,
        color: dark ? '#0f172a' : '#ffffff',
      },
    },
    grid: {
      vertLines: {
        color: dark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.22)',
      },
      horzLines: {
        color: dark ? 'rgba(148,163,184,0.08)' : 'rgba(148,163,184,0.22)',
      },
    },
    rightPriceScale: {
      borderColor: dark ? 'rgba(148,163,184,0.35)' : 'rgba(148,163,184,0.5)',
    },
    timeScale: {
      borderColor: dark ? 'rgba(148,163,184,0.35)' : 'rgba(148,163,184,0.5)',
      timeVisible: true,
      secondsVisible: false,
    },
  })

  candleSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#16a34a',
    downColor: '#dc2626',
    borderVisible: false,
    wickUpColor: '#16a34a',
    wickDownColor: '#dc2626',
  })

  resizeObserver = new ResizeObserver(() => {
    if (!chart || !host) {
      return
    }
    chart.applyOptions({
      width: host.clientWidth,
      height: host.clientHeight || 420,
    })
  })

  resizeObserver.observe(host)
}

function refreshChart(): void {
  ensureChart()
  if (!chart || !candleSeries) {
    return
  }

  const candles: CandlestickData<Time>[] = []

  sortedHistory.value.forEach((row) => {
    const time = toTimestamp(row.time)
    const open = toNumber(row.open)
    const high = toNumber(row.high)
    const low = toNumber(row.low)
    const close = toNumber(row.close)

    if (!time) return
    if (![open, high, low, close].every((value) => Number.isFinite(value) && value > 0)) {
      return
    }

    candles.push({
      time,
      open,
      high,
      low,
      close,
    })
  })

  candleSeries.setData(candles)
  if (candles.length > 0) {
    chart.timeScale().fitContent()
  }
}

function destroyChart(): void {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }

  if (chart) {
    chart.remove()
    chart = null
  }

  candleSeries = null
}

async function refreshAll(forceRefresh: boolean = true, notify: boolean = true): Promise<void> {
  if (isBusy.value) {
    return
  }

  isBusy.value = true
  loadingMessage.value = 'Đang tải dữ liệu thị trường...'

  try {
    const symbol = selectedSymbol.value

    const [snapshotResult, historyResult, technicalResult, newsResult, eventsResult, overviewResult] =
      await Promise.allSettled([
        stockBackendApi.getSnapshots([symbol], forceRefresh),
        stockBackendApi.getHistory(symbol, undefined, undefined, 320, forceRefresh),
        stockBackendApi.getTechnicalAnalysis(symbol, undefined, undefined, 320, forceRefresh),
        stockBackendApi.getMarketNews([symbol], 12, forceRefresh),
        stockBackendApi.getMarketEvents([symbol], 12, forceRefresh),
        stockBackendApi.getCompanyOverview(symbol, forceRefresh),
      ])

    if (snapshotResult.status === 'fulfilled') {
      snapshot.value =
        snapshotResult.value.data.find((item) => item.symbol.toUpperCase() === symbol.toUpperCase()) ||
        snapshotResult.value.data[0] ||
        null
    } else {
      snapshot.value = null
    }

    history.value = historyResult.status === 'fulfilled' ? historyResult.value.data : []
    technical.value = technicalResult.status === 'fulfilled' ? technicalResult.value : null
    newsItems.value = newsResult.status === 'fulfilled' ? newsResult.value.data : []
    eventItems.value = eventsResult.status === 'fulfilled' ? eventsResult.value.data : []
    overview.value = overviewResult.status === 'fulfilled' ? overviewResult.value : null

    backtestRecords.value = buildBacktestRecords()

    await nextTick()
    refreshChart()

    const hasData =
      snapshot.value !== null ||
      history.value.length > 0 ||
      technical.value !== null ||
      newsItems.value.length > 0

    status.value = hasData ? 'connected' : 'disconnected'

    if (hasData) {
      analysis.value = buildAnalysis()
      if (notify) {
        showAlert(`Đã cập nhật dữ liệu cho ${symbol}.`, 'success')
      }
    } else {
      showAlert(`Không có dữ liệu khả dụng cho ${symbol}.`, 'error')
    }
  } catch (error) {
    console.error('Failed to refresh AI analysis page', error)
    status.value = 'disconnected'
    showAlert('Không thể tải dữ liệu từ backend_v2.', 'error')
  } finally {
    isBusy.value = false
  }
}

async function generateAnalysis(notify: boolean): Promise<void> {
  if (isAnalyzing.value) {
    return
  }

  isAnalyzing.value = true
  status.value = 'analyzing'
  loadingMessage.value = 'Đang phân tích dữ liệu kỹ thuật và tin tức...'

  try {
    analysis.value = buildAnalysis()
    backtestRecords.value = buildBacktestRecords()

    if (notify) {
      showAlert(`Đã tạo báo cáo AI cho ${selectedSymbol.value}.`, 'success')
    }
  } finally {
    isAnalyzing.value = false
    status.value = 'connected'
  }
}

function rebuildBacktest(): void {
  backtestRecords.value = buildBacktestRecords()
  showAlert('Đã tính lại backtest từ dữ liệu lịch sử.', 'info')
}

async function onSymbolChange(): Promise<void> {
  await refreshAll(true, false)
  await generateAnalysis(false)
}

watch(
  () => sortedHistory.value,
  async () => {
    await nextTick()
    refreshChart()
  },
  { deep: true },
)

watch(isDarkTheme, () => {
  applyChartTheme()
})

onMounted(async () => {
  themeObserver = new MutationObserver(() => {
    isDarkTheme.value = document.documentElement.classList.contains('dark')
  })

  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  })

  await refreshAll(false, false)
  await generateAnalysis(false)
})

onUnmounted(() => {
  if (alertTimer) {
    clearTimeout(alertTimer)
  }

  if (themeObserver) {
    themeObserver.disconnect()
    themeObserver = null
  }

  destroyChart()
})
</script>
