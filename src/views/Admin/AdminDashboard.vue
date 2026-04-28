<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <PageHeader title="Quản trị hệ thống">
      <span class="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
        {{ activeTabMeta.label }}
      </span>
    </PageHeader>

    <div class="mx-auto max-w-7xl p-6">
      <div class="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside class="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-white/[0.03]">
          <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Tabs quản trị</p>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Tập trung toàn bộ tác vụ quản trị trên một màn hình duy nhất.
          </p>

          <div class="mt-4 hidden space-y-2 lg:block">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="flex w-full items-start gap-3 rounded-xl border px-4 py-3 text-left transition-colors"
              :class="activeTab === tab.key ? 'border-brand-500 bg-brand-50 dark:border-brand-500/60 dark:bg-brand-500/10' : 'border-gray-200 bg-gray-50 hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800/60 dark:hover:bg-gray-800'"
              @click="setActiveTab(tab.key)"
            >
              <span class="mt-0.5 flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold" :class="tab.badgeClass">
                {{ tab.shortLabel }}
              </span>
              <span class="min-w-0">
                <span class="block text-sm font-semibold text-gray-800 dark:text-white/90">{{ tab.label }}</span>
                <span class="mt-0.5 block text-xs leading-5 text-gray-500 dark:text-gray-400">{{ tab.description }}</span>
              </span>
            </button>
          </div>

          <div class="mt-4 flex gap-2 overflow-x-auto pb-1 lg:hidden">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="whitespace-nowrap rounded-full border px-4 py-2 text-sm font-medium transition-colors"
              :class="activeTab === tab.key ? 'border-brand-500 bg-brand-500 text-white' : 'border-gray-200 bg-white text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300'"
              @click="setActiveTab(tab.key)"
            >
              {{ tab.label }}
            </button>
          </div>
        </aside>

        <section class="min-w-0">
          <component :is="activeComponent" />
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import TabRevenue from './components/TabRevenue.vue'
import TabUsers from './components/TabUsers.vue'
import TabPortfolios from './components/TabPortfolios.vue'
import TabPromotions from './components/TabPromotions.vue'
import TabFlashSales from './components/TabFlashSales.vue'
import TabEtlMonitor from './components/TabEtlMonitor.vue'

type AdminTab = 'revenue' | 'users' | 'portfolios' | 'promotions' | 'flash-sales' | 'etl-monitor'

const tabs: Array<{
  key: AdminTab
  label: string
  shortLabel: string
  description: string
  badgeClass: string
}> = [
  {
    key: 'revenue',
    label: 'Tổng quan',
    shortLabel: 'R',
    description: 'Doanh thu, premium và tăng trưởng theo tháng.',
    badgeClass: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300',
  },
  {
    key: 'users',
    label: 'Người dùng',
    shortLabel: 'U',
    description: 'Danh sách, đổi quyền, khóa và mở khóa tài khoản.',
    badgeClass: 'bg-brand-100 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300',
  },
  {
    key: 'portfolios',
    label: 'Danh mục khách hàng',
    shortLabel: 'P',
    description: 'Theo dõi các mã đang được người dùng quan tâm.',
    badgeClass: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300',
  },
  {
    key: 'promotions',
    label: 'Khuyến mãi',
    shortLabel: 'K',
    description: 'Quản trị mã giảm giá premium và thời gian áp dụng.',
    badgeClass: 'bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300',
  },
  {
    key: 'flash-sales',
    label: 'Flash Sale',
    shortLabel: 'F',
    description: 'Tạo ưu đãi hệ thống tự động áp dụng cho checkout.',
    badgeClass: 'bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300',
  },
  {
    key: 'etl-monitor',
    label: 'ETL Monitor',
    shortLabel: 'E',
    description: 'Theo dõi pipeline dữ liệu, snapshot, health và lịch sử chạy.',
    badgeClass: 'bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300',
  },
]

const route = useRoute()
const router = useRouter()
const activeTab = ref<AdminTab>('revenue')

const activeComponent = computed(() => {
  if (activeTab.value === 'users') return TabUsers
  if (activeTab.value === 'portfolios') return TabPortfolios
  if (activeTab.value === 'promotions') return TabPromotions
  if (activeTab.value === 'flash-sales') return TabFlashSales
  if (activeTab.value === 'etl-monitor') return TabEtlMonitor
  return TabRevenue
})

const activeTabMeta = computed(() => tabs.find((tab) => tab.key === activeTab.value) || tabs[0])

function resolveTab(value: unknown): AdminTab {
  return value === 'users' || value === 'portfolios' || value === 'promotions' || value === 'flash-sales' || value === 'etl-monitor' ? value : 'revenue'
}

function setActiveTab(tab: AdminTab): void {
  activeTab.value = tab
  router.replace({
    path: '/admin',
    query: tab === 'revenue' ? {} : { tab },
  })
}

watch(
  () => route.query.tab,
  (value) => {
    activeTab.value = resolveTab(value)
  },
  { immediate: true },
)
</script>
