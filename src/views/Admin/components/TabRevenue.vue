<template>
  <div class="space-y-6">
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
        <p class="text-sm text-gray-500 dark:text-gray-400">Tổng doanh thu</p>
        <p class="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{{ formatPrice(stats?.total_revenue || 0) }}₫</p>
      </div>
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
        <p class="text-sm text-gray-500 dark:text-gray-400">Giao dịch hoàn tất</p>
        <p class="mt-2 text-2xl font-bold text-brand-600 dark:text-brand-400">{{ stats?.total_subscriptions || 0 }}</p>
      </div>
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
        <p class="text-sm text-gray-500 dark:text-gray-400">Premium đang hoạt động</p>
        <p class="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400">{{ stats?.active_premium_count || 0 }}</p>
      </div>
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
        <p class="text-sm text-gray-500 dark:text-gray-400">Tổng người dùng</p>
        <p class="mt-2 text-2xl font-bold text-purple-600 dark:text-purple-400">{{ stats?.total_users || 0 }}</p>
      </div>
    </div>

    <div class="rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
      <div class="flex items-center justify-between border-b border-gray-100 px-6 py-4 dark:border-gray-800">
        <div>
          <h2 class="text-lg font-semibold text-gray-800 dark:text-white/90">Doanh thu theo tháng</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">Dữ liệu lấy từ API quản trị hiện tại.</p>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center py-16">
        <div class="h-10 w-10 animate-spin rounded-full border-b-2 border-brand-500"></div>
      </div>

      <div v-else-if="error" class="px-6 py-8">
        <div class="rounded-xl border border-error-200 bg-error-50 px-4 py-3 text-sm text-error-700 dark:border-error-500/30 dark:bg-error-500/10 dark:text-error-300">
          {{ error }}
        </div>
      </div>

      <div v-else-if="!stats || stats.monthly_revenue.length === 0" class="px-6 py-10 text-center text-gray-500 dark:text-gray-400">
        Chưa có dữ liệu doanh thu.
      </div>

      <div v-else class="overflow-hidden">
        <table class="w-full min-w-[720px]">
          <thead class="bg-gray-50 dark:bg-gray-800/80">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Tháng</th>
              <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Doanh thu</th>
              <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Giao dịch</th>
              <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Biểu đồ</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
            <tr v-for="row in stats.monthly_revenue" :key="row.month" class="hover:bg-gray-50 dark:hover:bg-gray-800/60">
              <td class="px-6 py-4 font-medium text-gray-800 dark:text-gray-200">{{ row.month }}</td>
              <td class="px-6 py-4 text-right font-mono text-emerald-600 dark:text-emerald-400">{{ formatPrice(row.revenue) }}₫</td>
              <td class="px-6 py-4 text-right text-sm text-gray-600 dark:text-gray-400">{{ row.count }}</td>
              <td class="px-6 py-4">
                <div class="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                  <div class="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600 transition-all" :style="{ width: barWidth(row.revenue) }"></div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getAdminSalesStats, type SalesStats } from '@/services/authApi'

const stats = ref<SalesStats | null>(null)
const loading = ref(true)
const error = ref('')

function formatPrice(value: number): string {
  return new Intl.NumberFormat('vi-VN').format(value)
}

function barWidth(revenue: number): string {
  if (!stats.value || stats.value.monthly_revenue.length === 0) return '0%'
  const max = Math.max(...stats.value.monthly_revenue.map((row) => row.revenue))
  if (max <= 0) return '0%'
  return `${Math.max(5, (revenue / max) * 100)}%`
}

async function loadStats(): Promise<void> {
  loading.value = true
  error.value = ''

  try {
    stats.value = await getAdminSalesStats()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Lỗi tải dữ liệu doanh thu.'
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>
