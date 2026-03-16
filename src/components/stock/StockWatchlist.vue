<template>
  <div
    class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] sm:p-6"
  >
    <div class="flex items-center justify-between mb-5">
      <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90">Danh mục theo dõi</h3>

      <div class="relative h-fit">
        <DropdownMenu :menu-items="menuItems">
          <template #icon>
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                fill-rule="evenodd"
                clip-rule="evenodd"
                d="M10.2441 6C10.2441 5.0335 11.0276 4.25 11.9941 4.25H12.0041C12.9706 4.25 13.7541 5.0335 13.7541 6C13.7541 6.9665 12.9706 7.75 12.0041 7.75H11.9941C11.0276 7.75 10.2441 6.9665 10.2441 6ZM10.2441 18C10.2441 17.0335 11.0276 16.25 11.9941 16.25H12.0041C12.9706 16.25 13.7541 17.0335 13.7541 18C13.7541 18.9665 12.9706 19.75 12.0041 19.75H11.9941C11.0276 19.75 10.2441 18.9665 10.2441 18ZM11.9941 10.25C11.0276 10.25 10.2441 11.0335 10.2441 12C10.2441 12.9665 11.0276 13.75 11.9941 13.75H12.0041C12.9706 13.75 13.7541 12.9665 13.7541 12C13.7541 11.0335 12.9706 10.25 12.0041 10.25H11.9941Z"
                fill="currentColor"
              />
            </svg>
          </template>
        </DropdownMenu>
      </div>
    </div>

    <!-- Watchlist items -->
    <div class="space-y-4 max-h-[400px] overflow-y-auto custom-scrollbar">
      <div
        v-for="stock in stocks"
        :key="stock.symbol"
        class="flex items-center justify-between p-3 rounded-xl transition-colors hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer"
        @click="$emit('select', stock.symbol)"
      >
        <div class="flex items-center gap-3">
          <!-- Logo -->
          <div
            class="flex items-center justify-center w-10 h-10 rounded-full text-white font-bold text-sm"
            :style="{ backgroundColor: stock.logoColor || '#465FFF' }"
          >
            {{ stock.symbol.substring(0, 2) }}
          </div>

          <!-- Symbol + Company -->
          <div>
            <h4 class="font-semibold text-sm text-gray-800 dark:text-white/90">
              {{ stock.symbol }}
            </h4>
            <p class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[100px]">
              {{ stock.companyName }}
            </p>
          </div>
        </div>

        <!-- Price + Change -->
        <div class="text-right">
          <p class="font-semibold text-sm text-gray-800 dark:text-white/90">
            {{ formatPrice(stock.price) }}
          </p>
          <span
            :class="[
              'text-xs font-medium',
              stock.changePercent >= 0
                ? 'text-success-600 dark:text-success-500'
                : 'text-error-600 dark:text-error-500',
            ]"
          >
            {{ stock.changePercent >= 0 ? '↑' : '↓' }}
            {{ Math.abs(stock.changePercent).toFixed(2) }}%
          </span>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-if="!stocks || stocks.length === 0"
        class="text-center py-8 text-gray-400 dark:text-gray-500"
      >
        <p class="text-sm">Chưa có mã nào trong watchlist</p>
        <p class="text-xs mt-1">Thêm mã cổ phiếu để theo dõi</p>
      </div>
    </div>

    <!-- Add stock input -->
    <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
      <div class="flex gap-2">
        <input
          v-model="newSymbol"
          type="text"
          placeholder="Thêm mã CK (VD: FPT)"
          class="flex-1 rounded-lg border border-gray-300 bg-transparent px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:text-white/90"
          @keyup.enter="addSymbol"
          maxlength="10"
        />
        <button
          @click="addSymbol"
          class="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600 transition-colors"
        >
          Thêm
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DropdownMenu from '@/components/common/DropdownMenu.vue'
import type { StockState } from '@/composables/useStockData'

defineProps<{
  stocks: StockState[]
}>()

const emit = defineEmits<{
  (e: 'select', symbol: string): void
  (e: 'add', symbol: string): void
  (e: 'remove', symbol: string): void
}>()

const menuItems = [
  { label: 'Sắp xếp theo giá', onClick: () => console.log('Sắp xếp theo giá') },
  { label: 'Sắp xếp theo % thay đổi', onClick: () => console.log('Sắp xếp theo thay đổi') },
]

const newSymbol = ref('')

function addSymbol() {
  const symbol = newSymbol.value.trim().toUpperCase()
  if (symbol && symbol.length >= 2) {
    emit('add', symbol)
    newSymbol.value = ''
  }
}

function formatPrice(price: number): string {
  if (price >= 1000) {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }
  return new Intl.NumberFormat('vi-VN').format(price)
}
</script>
