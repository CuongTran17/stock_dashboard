<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <PageHeader title="📊 Danh mục của tôi" />

    <div class="p-6">
      <div class="flex items-center justify-between mb-8">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">📊 Danh mục của tôi</h1>
        <button
          @click="showAddModal = true"
          class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Thêm mã
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-12">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
      </div>

      <!-- Empty state -->
      <div v-else-if="items.length === 0" class="text-center py-16">
        <div class="text-6xl mb-4">📭</div>
        <p class="text-gray-500 dark:text-gray-400 mb-4">Chưa có mã cổ phiếu nào trong danh mục</p>
        <button @click="showAddModal = true" class="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors">
          Thêm mã đầu tiên
        </button>
      </div>

      <!-- Portfolio Table -->
      <div v-else class="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Mã CK</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Số lượng</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Giá TB</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Ghi chú</th>
              <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-for="item in items" :key="item.id" class="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
              <td class="px-6 py-4">
                <router-link :to="`/stocks/${item.symbol}`" class="font-semibold text-brand-600 hover:underline">
                  {{ item.symbol }}
                </router-link>
              </td>
              <td class="px-6 py-4 text-right font-mono text-sm">{{ item.quantity.toLocaleString() }}</td>
              <td class="px-6 py-4 text-right font-mono text-sm">{{ item.avg_price ? formatPrice(item.avg_price) : '—' }}</td>
              <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 max-w-[200px] truncate">{{ item.note || '—' }}</td>
              <td class="px-6 py-4 text-center">
                <button @click="handleRemove(item.symbol)" class="text-red-500 hover:text-red-700 text-sm transition-colors">
                  Xóa
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Modal -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" @click.self="showAddModal = false">
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Thêm vào danh mục</h3>
        <form @submit.prevent="handleAdd" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Mã cổ phiếu</label>
            <input
              v-model="newSymbol"
              type="text"
              maxlength="10"
              placeholder="VD: FPT"
              required
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none uppercase"
            />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Số lượng</label>
              <input
                v-model.number="newQuantity"
                type="number"
                min="0"
                placeholder="0"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Giá TB</label>
              <input
                v-model.number="newAvgPrice"
                type="number"
                min="0"
                step="100"
                placeholder="0"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Ghi chú</label>
            <input
              v-model="newNote"
              type="text"
              placeholder="Tùy chọn..."
              class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
          <div class="flex gap-3 pt-2">
            <button
              type="button"
              @click="showAddModal = false"
              class="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Hủy
            </button>
            <button
              type="submit"
              :disabled="addLoading"
              class="flex-1 px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors disabled:opacity-50"
            >
              {{ addLoading ? 'Đang thêm...' : 'Thêm' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import { addToPortfolio, getMyPortfolio, removeFromPortfolio, type PortfolioItem } from '@/services/authApi'

const items = ref<PortfolioItem[]>([])
const loading = ref(true)
const showAddModal = ref(false)
const addLoading = ref(false)

const newSymbol = ref('')
const newQuantity = ref(0)
const newAvgPrice = ref<number | undefined>(undefined)
const newNote = ref('')

function formatPrice(n: number): string {
  return n.toLocaleString('vi-VN')
}

async function loadPortfolio() {
  loading.value = true
  try {
    const data = await getMyPortfolio()
    items.value = data.items
  } catch (e) {
    console.error('Failed to load portfolio:', e)
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!newSymbol.value.trim()) return
  addLoading.value = true
  try {
    await addToPortfolio(newSymbol.value, newQuantity.value, newAvgPrice.value, newNote.value || undefined)
    showAddModal.value = false
    newSymbol.value = ''
    newQuantity.value = 0
    newAvgPrice.value = undefined
    newNote.value = ''
    await loadPortfolio()
  } catch (e: any) {
    alert(e.message || 'Lỗi khi thêm mã')
  } finally {
    addLoading.value = false
  }
}

async function handleRemove(symbol: string) {
  if (!confirm(`Xóa ${symbol} khỏi danh mục?`)) return
  try {
    await removeFromPortfolio(symbol)
    await loadPortfolio()
  } catch (e: any) {
    alert(e.message || 'Lỗi khi xóa mã')
  }
}

onMounted(loadPortfolio)
</script>
