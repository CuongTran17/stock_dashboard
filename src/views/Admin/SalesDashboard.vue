<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <PageHeader title="📈 Dashboard Doanh Thu Premium" />
    <div class="p-6">
      <div class="max-w-6xl mx-auto">
        <!-- Loading -->
        <div v-if="loading" class="text-center py-12">
          <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-brand-500 mx-auto"></div>
        </div>

        <template v-else-if="stats">
          <!-- Stats Cards -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
              <p class="text-sm text-gray-500 dark:text-gray-400">Tổng doanh thu</p>
              <p class="text-2xl font-bold text-emerald-600 mt-1">{{ formatPrice(stats.total_revenue) }}₫</p>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
              <p class="text-sm text-gray-500 dark:text-gray-400">Tổng giao dịch hoàn tất</p>
              <p class="text-2xl font-bold text-brand-600 mt-1">{{ stats.total_subscriptions }}</p>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
              <p class="text-sm text-gray-500 dark:text-gray-400">Premium đang hoạt động</p>
              <p class="text-2xl font-bold text-amber-600 mt-1">{{ stats.active_premium_count }}</p>
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
              <p class="text-sm text-gray-500 dark:text-gray-400">Tổng người dùng</p>
              <p class="text-2xl font-bold text-purple-600 mt-1">{{ stats.total_users }}</p>
            </div>
          </div>

          <!-- Monthly Revenue Chart (Table) -->
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">Doanh thu theo tháng</h2>
            </div>
            <div v-if="stats.monthly_revenue.length === 0" class="p-6 text-center text-gray-500 dark:text-gray-400">
              Chưa có dữ liệu doanh thu.
            </div>
            <table v-else class="w-full">
              <thead class="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Tháng</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Doanh thu</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Số giao dịch</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Biểu đồ</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
                <tr v-for="row in stats.monthly_revenue" :key="row.month" class="hover:bg-gray-50 dark:hover:bg-gray-750">
                  <td class="px-6 py-4 font-medium text-gray-800 dark:text-gray-200">{{ row.month }}</td>
                  <td class="px-6 py-4 text-right font-mono text-emerald-600 font-semibold">{{ formatPrice(row.revenue) }}₫</td>
                  <td class="px-6 py-4 text-right text-sm text-gray-600 dark:text-gray-400">{{ row.count }}</td>
                  <td class="px-6 py-4">
                    <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                      <div
                        class="bg-gradient-to-r from-emerald-400 to-emerald-600 h-2 rounded-full transition-all"
                        :style="{ width: barWidth(row.revenue) }"
                      ></div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <div v-else-if="error" class="text-center py-12">
          <p class="text-red-500">{{ error }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import { getAdminSalesStats, type SalesStats } from '@/services/authApi'

const stats = ref<SalesStats | null>(null)
const loading = ref(true)
const error = ref('')

function formatPrice(n: number): string {
  return n.toLocaleString('vi-VN')
}

function barWidth(revenue: number): string {
  if (!stats.value || stats.value.monthly_revenue.length === 0) return '0%'
  const max = Math.max(...stats.value.monthly_revenue.map((r) => r.revenue))
  if (max <= 0) return '0%'
  return `${Math.max(5, (revenue / max) * 100)}%`
}

async function loadStats() {
  loading.value = true
  try {
    stats.value = await getAdminSalesStats()
  } catch (e: any) {
    error.value = e.message || 'Lỗi tải dữ liệu'
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>
