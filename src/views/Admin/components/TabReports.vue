<template>
  <div class="space-y-5">
    <div class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
      <div class="border-b border-gray-100 px-5 py-4 dark:border-gray-800">
        <div class="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-brand-600 dark:text-brand-400">Trung tâm báo cáo</p>
            <h2 class="mt-1 text-lg font-semibold text-gray-900 dark:text-white">Báo cáo quản trị</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Theo dõi doanh thu, người dùng và đơn hàng theo khoảng thời gian tùy chọn.
            </p>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              class="inline-flex items-center rounded-lg border border-gray-200 bg-white px-3.5 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
              :disabled="loading"
              @click="loadReport"
            >
              Xem trước
            </button>
            <button
              class="inline-flex items-center rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="exporting !== ''"
              @click="exportReport('xlsx')"
            >
              {{ exporting === 'xlsx' ? 'Đang xuất...' : 'Excel' }}
            </button>
            <button
              class="inline-flex items-center rounded-lg bg-rose-600 px-3.5 py-2 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="exporting !== ''"
              @click="exportReport('pdf')"
            >
              {{ exporting === 'pdf' ? 'Đang xuất...' : 'PDF' }}
            </button>
          </div>
        </div>
      </div>

      <div class="space-y-4 p-5">
        <div class="grid gap-4 xl:grid-cols-[1.2fr_1.4fr_1fr]">
          <div>
            <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Loại báo cáo</p>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="option in reportTypeOptions"
                :key="option.value"
                class="rounded-lg border px-3 py-2 text-sm font-medium transition"
                :class="filters.report_type === option.value ? activeFilterClass : idleFilterClass"
                @click="filters.report_type = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>

          <div>
            <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Khoảng thời gian</p>
            <div class="grid grid-cols-3 gap-2 lg:grid-cols-6">
              <button
                v-for="option in periodOptions"
                :key="option.value"
                class="rounded-lg border px-3 py-2 text-sm font-medium transition"
                :class="filters.period === option.value ? activeFilterClass : idleFilterClass"
                @click="filters.period = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>

          <label class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Sắp xếp
            <select
              v-model="filters.sort"
              class="mt-2 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 outline-none transition focus:border-brand-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
            >
              <option value="asc">Cũ nhất trước</option>
              <option value="desc">Mới nhất trước</option>
            </select>
          </label>
        </div>

        <div class="grid gap-3 md:grid-cols-3">
          <label class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Ngày mốc
            <input
              v-model="filters.anchor_date"
              type="date"
              :disabled="filters.period === 'custom' || filters.period === 'all'"
              class="mt-2 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 outline-none transition focus:border-brand-500 disabled:bg-gray-100 disabled:text-gray-400 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:disabled:bg-gray-900"
            />
          </label>
          <label class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Từ ngày
            <input
              v-model="filters.start_date"
              type="date"
              :disabled="filters.period !== 'custom'"
              class="mt-2 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 outline-none transition focus:border-brand-500 disabled:bg-gray-100 disabled:text-gray-400 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:disabled:bg-gray-900"
            />
          </label>
          <label class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
            Đến ngày
            <input
              v-model="filters.end_date"
              type="date"
              :disabled="filters.period !== 'custom'"
              class="mt-2 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 outline-none transition focus:border-brand-500 disabled:bg-gray-100 disabled:text-gray-400 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:disabled:bg-gray-900"
            />
          </label>
        </div>

        <div v-if="error" class="rounded-lg border border-error-200 bg-error-50 px-4 py-3 text-sm text-error-700 dark:border-error-500/30 dark:bg-error-500/10 dark:text-error-300">
          {{ error }}
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center rounded-lg border border-gray-200 bg-white py-16 dark:border-gray-800 dark:bg-white/[0.03]">
      <div class="h-10 w-10 animate-spin rounded-full border-b-2 border-brand-500"></div>
    </div>

    <div v-else-if="report" class="space-y-5">
      <div class="rounded-lg border border-gray-200 bg-white px-5 py-4 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ bucketLabel(report.range.bucket) }}</p>
            <h3 class="mt-1 text-base font-semibold text-gray-900 dark:text-white">{{ report.range.label }}</h3>
          </div>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{ report.range.start_date || 'Tất cả' }} - {{ report.range.end_date || 'Tất cả' }}
          </p>
        </div>
      </div>

      <section
        v-for="(section, sectionKey) in report.sections"
        :key="sectionKey"
        class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-white/[0.03]"
      >
        <div class="flex flex-col gap-1 border-b border-gray-100 px-5 py-4 dark:border-gray-800 sm:flex-row sm:items-center sm:justify-between">
          <h3 class="text-base font-semibold text-gray-900 dark:text-white">{{ section.title }}</h3>
          <span class="text-xs font-medium text-gray-500 dark:text-gray-400">{{ section.details.length }} dòng chi tiết</span>
        </div>

        <div class="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-4">
          <div
            v-for="(value, key) in section.summary"
            :key="key"
            class="rounded-lg border border-gray-100 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900/40"
          >
            <p class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ formatKey(String(key)) }}</p>
            <p class="mt-2 text-xl font-semibold text-gray-900 dark:text-white">{{ formatValue(String(key), value) }}</p>
          </div>
        </div>

        <div class="overflow-x-auto border-t border-gray-100 dark:border-gray-800">
          <table class="w-full min-w-[720px]">
            <thead class="bg-gray-50 dark:bg-gray-800/80">
              <tr>
                <th
                  v-for="header in detailHeaders(section.details)"
                  :key="header"
                  class="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400"
                >
                  {{ formatKey(header) }}
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
              <tr v-if="section.details.length === 0">
                <td class="px-5 py-8 text-center text-sm text-gray-500 dark:text-gray-400" :colspan="detailHeaders(section.details).length || 1">
                  Không có dữ liệu.
                </td>
              </tr>
              <tr v-for="(row, index) in section.details" :key="`${sectionKey}-${index}`" class="hover:bg-gray-50 dark:hover:bg-gray-800/60">
                <td
                  v-for="header in detailHeaders(section.details)"
                  :key="header"
                  class="px-5 py-3.5 text-sm text-gray-600 dark:text-gray-300"
                  :class="isNumber(row[header]) ? 'text-right tabular-nums' : ''"
                >
                  {{ formatValue(header, row[header]) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import {
  downloadAdminReport,
  getAdminReport,
  type AdminReportFilters,
  type AdminReportFormat,
  type AdminReportPeriod,
  type AdminReportResponse,
  type AdminReportType,
} from '@/services/authApi'

const today = new Date().toISOString().slice(0, 10)
const filters = reactive<AdminReportFilters>({
  report_type: 'summary',
  period: 'month',
  anchor_date: today,
  start_date: '',
  end_date: '',
  sort: 'asc',
})
const report = ref<AdminReportResponse | null>(null)
const loading = ref(false)
const exporting = ref<AdminReportFormat | ''>('')
const error = ref('')

const activeFilterClass = 'border-brand-500 bg-brand-50 text-brand-700 dark:border-brand-400/70 dark:bg-brand-500/15 dark:text-brand-200'
const idleFilterClass = 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700'

const reportTypeOptions: { value: AdminReportType; label: string }[] = [
  { value: 'summary', label: 'Tổng hợp' },
  { value: 'revenue', label: 'Doanh thu' },
  { value: 'users', label: 'Người dùng' },
  { value: 'orders', label: 'Đơn hàng' },
]

const periodOptions: { value: AdminReportPeriod; label: string }[] = [
  { value: 'day', label: 'Ngày' },
  { value: 'month', label: 'Tháng' },
  { value: 'quarter', label: 'Quý' },
  { value: 'year', label: 'Năm' },
  { value: 'all', label: 'Tất cả' },
  { value: 'custom', label: 'Tùy chọn' },
]

function normalizedFilters(): AdminReportFilters {
  return {
    report_type: filters.report_type,
    period: filters.period,
    sort: filters.sort,
    anchor_date: filters.period === 'custom' || filters.period === 'all' ? undefined : filters.anchor_date,
    start_date: filters.period === 'custom' ? filters.start_date : undefined,
    end_date: filters.period === 'custom' ? filters.end_date : undefined,
  }
}

async function loadReport(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    report.value = await getAdminReport(normalizedFilters())
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Không tải được báo cáo.'
  } finally {
    loading.value = false
  }
}

async function exportReport(format: AdminReportFormat): Promise<void> {
  exporting.value = format
  error.value = ''
  try {
    const currentReport = report.value || (await getAdminReport(normalizedFilters()))
    report.value = currentReport
    const blob = await downloadAdminReport(normalizedFilters(), format)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const range = currentReport.range
    link.href = url
    link.download = `admin_report_${filters.report_type}_${range.start_date || 'all'}_${range.end_date || 'all'}.${format}`
    link.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Không xuất được báo cáo.'
  } finally {
    exporting.value = ''
  }
}

function detailHeaders(rows: Record<string, number | string>[]): string[] {
  return rows[0] ? Object.keys(rows[0]) : ['date']
}

function formatKey(value: string): string {
  const labels: Record<string, string> = {
    date: 'Thời gian',
    revenue: 'Doanh thu',
    orders: 'Đơn hàng',
    completed_orders: 'GD hoàn tất',
    average_order_value: 'TB/GD',
    total_revenue: 'Tổng doanh thu',
    new_users: 'Người dùng mới',
    premium_users: 'Premium',
    locked_users: 'Bị khóa',
    completed: 'Hoàn tất',
    pending: 'Đang chờ',
    cancelled: 'Đã hủy',
  }
  return labels[value] || value.replace(/_/g, ' ')
}

function formatValue(key: string, value: number | string): string {
  if (typeof value === 'number' && (key.includes('revenue') || key.includes('value') || key.includes('amount'))) {
    return value.toLocaleString('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 })
  }
  if (typeof value === 'number') return value.toLocaleString('vi-VN')
  return String(value)
}

function isNumber(value: unknown): boolean {
  return typeof value === 'number'
}

function bucketLabel(bucket: string): string {
  const labels: Record<string, string> = {
    day: 'Theo ngày',
    month: 'Theo tháng',
    quarter: 'Theo quý',
    year: 'Theo năm',
    all: 'Tất cả',
  }
  return labels[bucket] || bucket
}

watch(
  () => [filters.report_type, filters.period, filters.anchor_date, filters.start_date, filters.end_date, filters.sort],
  () => {
    if (filters.period !== 'custom') {
      void loadReport()
    }
  },
)

onMounted(loadReport)
</script>
