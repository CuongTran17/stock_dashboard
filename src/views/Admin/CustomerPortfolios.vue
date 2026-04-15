<template>
  <div class="min-h-screen bg-gray-50 p-6 dark:bg-gray-900">
    <div class="mx-auto max-w-6xl space-y-6">
      <div class="flex flex-col gap-2">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Danh mục khách hàng</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">Theo dõi vị thế của người dùng cùng mức TP/SL đã đặt.</p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
      </div>

      <!-- Empty -->
      <div v-else-if="portfolios.length === 0" class="text-center py-16">
        <div class="text-6xl mb-4">📋</div>
        <p class="text-gray-500 dark:text-gray-400">Chưa có khách hàng nào tạo danh mục đầu tư.</p>
      </div>

      <!-- Customer Cards -->
      <div v-else class="space-y-6">
        <div
          v-for="portfolio in portfolios"
          :key="portfolio.user.id"
          class="overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
        >
          <!-- User Header -->
          <div class="px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-750 dark:to-gray-700 flex items-center justify-between">
            <div>
              <h3 class="font-semibold text-gray-800 dark:text-gray-200">{{ portfolio.user.fullname }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ portfolio.user.email }}</p>
            </div>
            <div class="flex items-center gap-3">
              <span
                :class="[
                  'px-3 py-1 text-xs font-medium rounded-full',
                  portfolio.user.role === 'premium'
                    ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                    : portfolio.user.role === 'admin'
                    ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    : 'bg-gray-100 text-gray-600 dark:bg-gray-600 dark:text-gray-300',
                ]"
              >
                {{ portfolio.user.role.toUpperCase() }}
              </span>
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ portfolio.total_symbols }} mã</span>
            </div>
          </div>

          <!-- Holdings Table -->
          <table class="w-full" v-if="portfolio.holdings.length > 0">
            <thead class="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th class="px-6 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Mã</th>
                <th class="px-6 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">SL</th>
                <th class="px-6 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Giá TB</th>
                <th class="px-6 py-2 text-right text-xs font-medium text-success-700 dark:text-success-400 uppercase">Giá TP</th>
                <th class="px-6 py-2 text-right text-xs font-medium text-error-700 dark:text-error-400 uppercase">Giá SL</th>
                <th class="px-6 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Ghi chú</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
              <tr v-for="h in portfolio.holdings" :key="h.symbol" class="hover:bg-gray-50 dark:hover:bg-gray-750">
                <td class="px-6 py-3 font-semibold text-blue-600">{{ h.symbol }}</td>
                <td class="px-6 py-3 text-right font-mono text-sm">{{ h.quantity.toLocaleString() }}</td>
                <td class="px-6 py-3 text-right font-mono text-sm">{{ h.avg_price ? h.avg_price.toLocaleString('vi-VN') : '—' }}</td>
                <td class="px-6 py-3 text-right font-mono text-sm text-success-700 dark:text-success-400">{{ h.tp_price ? h.tp_price.toLocaleString('vi-VN') : '—' }}</td>
                <td class="px-6 py-3 text-right font-mono text-sm text-error-700 dark:text-error-400">{{ h.sl_price ? h.sl_price.toLocaleString('vi-VN') : '—' }}</td>
                <td class="px-6 py-3 text-sm text-gray-500 dark:text-gray-400">{{ h.note || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="total > perPage" class="flex justify-center gap-2 mt-6">
          <button
            @click="changePage(page - 1)"
            :disabled="page <= 1"
            class="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            ‹ Trước
          </button>
          <span class="px-4 py-2 text-sm text-gray-500 dark:text-gray-400">Trang {{ page }}</span>
          <button
            @click="changePage(page + 1)"
            :disabled="portfolios.length < perPage"
            class="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            Sau ›
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAdminUserPortfolios, type AdminUserPortfolio } from '@/services/authApi'

const portfolios = ref<AdminUserPortfolio[]>([])
const loading = ref(true)
const page = ref(1)
const perPage = 20
const total = ref(0)

async function loadPortfolios() {
  loading.value = true
  try {
    const data = await getAdminUserPortfolios(page.value, perPage)
    portfolios.value = data.portfolios
    total.value = data.total
  } catch (e: any) {
    console.error('Failed to load portfolios:', e)
  } finally {
    loading.value = false
  }
}

function changePage(newPage: number) {
  page.value = newPage
  loadPortfolios()
}

onMounted(loadPortfolios)
</script>
