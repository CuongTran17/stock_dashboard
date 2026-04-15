<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
    <!-- Header -->
    <div class="text-center mb-10">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-3">
        ⭐ Nâng cấp <span class="bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">Premium</span>
      </h1>
      <p class="text-gray-500 dark:text-gray-400 max-w-xl mx-auto">
        Mở khóa sức mạnh AI Trading-R1 để nhận phân tích chuyên sâu và khuyến nghị mua/bán cổ phiếu tự động hàng ngày.
      </p>
    </div>

    <!-- Pricing Card -->
    <div class="max-w-md mx-auto">
      <div class="relative bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-amber-200 dark:border-amber-700 overflow-hidden">
        <!-- Ribbon -->
        <div class="absolute top-4 right-[-35px] rotate-45 bg-gradient-to-r from-amber-400 to-orange-500 text-white text-xs font-bold py-1 px-10 shadow">
          HOT
        </div>

        <div class="p-8">
          <h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">Gói Premium AI</h2>
          <div class="flex items-baseline gap-1 mb-4">
            <span class="text-4xl font-extrabold text-amber-500">{{ formatPrice(paymentInfo?.amount || 99000) }}</span>
            <span class="text-gray-500 dark:text-gray-400 text-sm">₫ / tháng</span>
          </div>

          <ul class="space-y-3 mb-8">
            <li v-for="feature in features" :key="feature" class="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
              <svg class="w-5 h-5 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              {{ feature }}
            </li>
          </ul>

          <!-- Payment QR Section -->
          <div v-if="loading" class="text-center py-8">
            <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-amber-500 mx-auto"></div>
            <p class="text-gray-500 mt-3 text-sm">Đang tải thông tin thanh toán...</p>
          </div>

          <div v-else-if="paymentInfo" class="space-y-4">
            <div class="bg-gray-50 dark:bg-gray-700 rounded-xl p-4 text-center">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">Quét mã QR để thanh toán</p>
              <img
                :src="paymentInfo.qr_url"
                :alt="'QR Code thanh toán ' + paymentInfo.transfer_content"
                class="mx-auto rounded-lg shadow-md w-56 h-56 object-contain bg-white"
              />
            </div>

            <div class="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-500 dark:text-gray-400">Ngân hàng:</span>
                <span class="font-medium text-gray-800 dark:text-gray-200">{{ paymentInfo.bank_name }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500 dark:text-gray-400">Số tài khoản:</span>
                <span class="font-mono font-medium text-gray-800 dark:text-gray-200">{{ paymentInfo.account_number }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500 dark:text-gray-400">Chủ tài khoản:</span>
                <span class="font-medium text-gray-800 dark:text-gray-200">{{ paymentInfo.account_name }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500 dark:text-gray-400">Số tiền:</span>
                <span class="font-bold text-amber-600">{{ formatPrice(paymentInfo.amount) }}₫</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500 dark:text-gray-400">Nội dung CK:</span>
                <span class="font-mono font-bold text-red-600 dark:text-red-400">{{ paymentInfo.transfer_content }}</span>
              </div>
            </div>

            <p class="text-xs text-center text-gray-400 dark:text-gray-500">
              ⚡ Sau khi chuyển khoản, hệ thống sẽ tự động kích hoạt Premium trong vòng 1-2 phút.
            </p>
          </div>

          <div v-else-if="error" class="text-center py-6">
            <p class="text-red-500 text-sm">{{ error }}</p>
            <button @click="loadPaymentInfo" class="mt-3 text-sm text-amber-600 hover:underline">Thử lại</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPremiumPaymentInfo, type PaymentInfo } from '@/services/authApi'

const paymentInfo = ref<PaymentInfo | null>(null)
const loading = ref(true)
const error = ref('')

const features = [
  'Phân tích AI Trading-R1 không giới hạn',
  'Khuyến nghị Mua/Bán hàng ngày',
  'Chain-of-Thought reasoning chuyên sâu',
  'Xem lịch sử backtest model',
  'Hỗ trợ tư vấn từ Admin',
  'Truy cập sớm tính năng mới',
]

function formatPrice(n: number): string {
  return n.toLocaleString('vi-VN')
}

async function loadPaymentInfo() {
  loading.value = true
  error.value = ''
  try {
    paymentInfo.value = await getPremiumPaymentInfo()
  } catch (e: any) {
    error.value = e.message || 'Không thể tải thông tin thanh toán'
  } finally {
    loading.value = false
  }
}

onMounted(loadPaymentInfo)
</script>
