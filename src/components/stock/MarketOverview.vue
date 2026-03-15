<template>
  <div
    class="rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03] sm:p-6"
  >
    <h3 class="text-lg font-semibold text-gray-800 dark:text-white/90 mb-5">
      Market Overview
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
            class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer transition-colors"
            @click="$emit('select', stock.symbol)"
          >
            <td class="py-3">
              <div class="flex items-center gap-2">
                <div
                  class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                  :style="{ backgroundColor: stock.logoColor || '#465FFF' }"
                >
                  {{ stock.symbol.substring(0, 2) }}
                </div>
                <div>
                  <p class="font-semibold text-gray-800 dark:text-white/90">{{ stock.symbol }}</p>
                  <p class="text-xs text-gray-400 truncate max-w-[80px]">{{ stock.companyName }}</p>
                </div>
              </div>
            </td>
            <td class="py-3 text-right font-medium text-gray-800 dark:text-white/90">
              {{ formatPrice(stock.price) }}
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
  if (Math.abs(price) >= 1000) {
    return new Intl.NumberFormat('vi-VN').format(price)
  }
  return price.toFixed(0)
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
