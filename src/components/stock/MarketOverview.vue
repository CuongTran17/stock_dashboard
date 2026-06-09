<template>
  <div
    class="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]"
  >
    <h3 class="mb-5 text-lg font-semibold text-gray-800 dark:text-white/90">
      Tổng quan thị trường
    </h3>

    <div class="overflow-x-auto custom-scrollbar">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-700">
            <th class="py-3 text-left font-medium text-gray-500 dark:text-gray-400">Mã CK</th>
            <th class="py-3 text-right font-medium text-gray-500 dark:text-gray-400">Giá</th>
            <th class="py-3 text-right font-medium text-gray-500 dark:text-gray-400">Thay đổi</th>
            <th class="py-3 text-right font-medium text-gray-500 dark:text-gray-400">%</th>
            <th class="py-3 text-right font-medium text-gray-500 dark:text-gray-400">KL</th>
            <th class="py-3 text-right font-medium text-gray-500 dark:text-gray-400">Cao</th>
            <th class="py-3 text-right font-medium text-gray-500 dark:text-gray-400">Thấp</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="stock in stocks"
            :key="stock.symbol"
            class="cursor-pointer border-b border-gray-100 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-white/5"
            @click="$emit('select', stock.symbol)"
          >
            <td class="py-3">
              <div class="flex items-center gap-2">
                <div
                  class="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold text-white"
                  :style="{ backgroundColor: stock.logoColor || '#465FFF' }"
                >
                  {{ stock.symbol.substring(0, 2) }}
                </div>
                <div>
                  <p class="font-semibold text-gray-800 dark:text-white/90">{{ stock.symbol }}</p>
                  <p class="max-w-[80px] truncate text-xs text-gray-400">{{ stock.companyName }}</p>
                </div>
              </div>
            </td>
            <td class="py-3 text-right font-medium text-gray-800 dark:text-white/90">
              {{ formatStockPrice(stock) }}
            </td>
            <td
              class="py-3 text-right font-medium"
              :class="stock.change >= 0 ? 'text-success-600' : 'text-error-600'"
            >
              {{ stock.change >= 0 ? '+' : '' }}{{ formatPrice(stock.change) }}
            </td>
            <td class="py-3 text-right">
              <span
                :class="[
                  'inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-medium',
                  stock.changePercent >= 0
                    ? 'bg-success-50 text-success-600 dark:bg-success-500/15 dark:text-success-500'
                    : 'bg-error-50 text-error-600 dark:bg-error-500/15 dark:text-error-500',
                ]"
              >
                {{ stock.changePercent >= 0 ? '↑' : '↓' }}
                {{ Math.abs(stock.changePercent).toFixed(2) }}%
              </span>
            </td>
            <td class="py-3 text-right text-gray-600 dark:text-gray-300">
              {{ formatVolume(stock.volume) }}
            </td>
            <td class="py-3 text-right text-gray-600 dark:text-gray-300">
              {{ formatPrice(stock.high) }}
            </td>
            <td class="py-3 text-right text-gray-600 dark:text-gray-300">
              {{ formatPrice(stock.low) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { StockState } from '@/composables/useStockData'

defineProps<{
  stocks: StockState[]
}>()

defineEmits<{
  (e: 'select', symbol: string): void
}>()

function formatPrice(price: number): string {
  return new Intl.NumberFormat('vi-VN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price)
}

function hasUsableSnapshotPrice(stock: StockState): boolean {
  return stock.price > 0 && stock.dataStatus !== 'NO_DATA_IN_SNAPSHOT'
}

function formatStockPrice(stock: StockState): string {
  return hasUsableSnapshotPrice(stock) ? formatPrice(stock.price) : '--'
}

function formatVolume(volume: number): string {
  if (volume >= 1_000_000) {
    return (volume / 1_000_000).toFixed(1) + 'M'
  }
  if (volume >= 1_000) {
    return (volume / 1_000).toFixed(0) + 'K'
  }
  return volume.toString()
}
</script>
