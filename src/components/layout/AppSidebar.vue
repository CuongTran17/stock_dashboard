<template>
  <aside
    :class="[
      'fixed mt-16 flex flex-col lg:mt-0 top-0 px-5 left-0 bg-white dark:bg-gray-900 dark:border-gray-800 text-gray-900 h-screen transition-all duration-300 ease-in-out z-99999 border-r border-gray-200',
      {
        'lg:w-[290px]': isExpanded || isMobileOpen || isHovered,
        'lg:w-[90px]': !isExpanded && !isHovered,
        'translate-x-0 w-[290px]': isMobileOpen,
        '-translate-x-full': !isMobileOpen,
        'lg:translate-x-0': true,
      },
    ]"
    @mouseenter="!isExpanded && (isHovered = true)"
    @mouseleave="isHovered = false"
  >
    <div
      :class="[
        'py-8 flex',
        !isExpanded && !isHovered ? 'lg:justify-center' : 'justify-start',
      ]"
    >
      <router-link to="/">
        <img
          v-if="isExpanded || isHovered || isMobileOpen"
          class="dark:hidden"
          src="/images/logo/logo.svg"
          alt="Logo"
          width="150"
          height="40"
        />
        <img
          v-if="isExpanded || isHovered || isMobileOpen"
          class="hidden dark:block"
          src="/images/logo/logo-dark.svg"
          alt="Logo"
          width="150"
          height="40"
        />
        <img
          v-else
          src="/images/logo/logo-icon.svg"
          alt="Logo"
          width="32"
          height="32"
        />
      </router-link>
    </div>
    <div
      class="flex flex-col overflow-y-auto duration-300 ease-linear no-scrollbar"
    >
      <nav class="mb-6">
        <div class="flex flex-col gap-4">
          <div v-for="(menuGroup, groupIndex) in menuGroups" :key="groupIndex">
            <h2
              :class="[
                'mb-4 text-xs uppercase flex leading-[20px] text-gray-400',
                !isExpanded && !isHovered
                  ? 'lg:justify-center'
                  : 'justify-start',
              ]"
            >
              <template v-if="isExpanded || isHovered || isMobileOpen">
                {{ menuGroup.title }}
              </template>
              <HorizontalDots v-else />
            </h2>
            <ul class="flex flex-col gap-4">
              <li v-for="item in menuGroup.items" :key="item.name">
                <router-link
                  v-if="item.path"
                  :to="item.path"
                  @click="handleMenuClick($event, item.path)"
                  :class="[
                    'menu-item group',
                    {
                      'menu-item-active': isActive(item.path),
                      'menu-item-inactive': !isActive(item.path),
                    },
                  ]"
                >
                  <span
                    :class="[
                      isActive(item.path)
                        ? 'menu-item-icon-active'
                        : 'menu-item-icon-inactive',
                    ]"
                  >
                    <component :is="item.icon" />
                  </span>
                  <span
                    v-if="isExpanded || isHovered || isMobileOpen"
                    class="menu-item-text"
                    >{{ item.name }}</span
                  >
                </router-link>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  HorizontalDots,
  LayoutDashboardIcon,
  BarChartIcon,
  ListIcon,
  BellIcon,
  MailIcon,
  ChatIcon,
  PieChartIcon,
  UserCircleIcon,
  LogoutIcon,
  BoxCubeIcon,
} from '../../icons'
import StockChartIcon from '@/icons/StockChartIcon.vue'
import { useSidebar } from '@/composables/useSidebar'
import { isLoggedIn, isAdmin, isPremium, getSavedUser, logout as authLogout } from '@/services/authApi'

const route = useRoute()
const router = useRouter()

const { isExpanded, isMobileOpen, isHovered } = useSidebar()

const menuGroups = computed(() => {
  const groups = [
    {
      title: 'Thị trường',
      items: [
        { icon: StockChartIcon, name: 'Bảng điều khiển', path: '/' },
        { icon: LayoutDashboardIcon, name: 'Tổng quan thị trường', path: '/market-overview' },
        { icon: BarChartIcon, name: 'Chi tiết cổ phiếu', path: '/stocks/FPT' },
        { icon: ListIcon, name: 'Lọc cổ phiếu', path: '/screener' },
        { icon: BellIcon, name: 'Cảnh báo danh mục', path: '/portfolio-alerts' },
        { icon: MailIcon, name: 'Tin tức và sự kiện', path: '/news-events' },
        { icon: ChatIcon, name: 'Phân tích AI', path: '/ai-analysis' },
      ],
    },
  ]

  // Logged-in user menu
  if (isLoggedIn()) {
    const user = getSavedUser()
    const userItems: { icon: any; name: string; path: string }[] = [
      { icon: UserCircleIcon, name: 'Tài khoản của tôi', path: '/profile' },
      { icon: BoxCubeIcon, name: 'Danh mục của tôi', path: '/my-portfolio' },
    ]

    if (!isPremium()) {
      userItems.push({ icon: PieChartIcon, name: '⭐ Nâng cấp Premium', path: '/premium' })
    }

    userItems.push({ icon: LogoutIcon, name: 'Đăng xuất', path: '/logout' })

    groups.push({ title: 'Tài khoản', items: userItems })
  } else {
    groups.push({
      title: 'Tài khoản',
      items: [
        { icon: UserCircleIcon, name: 'Đăng nhập', path: '/signin' },
        { icon: UserCircleIcon, name: 'Đăng ký', path: '/signup' },
      ],
    })
  }

  // Admin menu
  if (isAdmin()) {
    groups.push({
      title: 'Quản trị',
      items: [
        { icon: LayoutDashboardIcon, name: 'Quản trị hệ thống', path: '/admin' },
      ],
    })
  }

  return groups
})

function isActive(path: string): boolean {
  if (path === '/logout') {
    return false
  }
  if (path.startsWith('/stocks/')) {
    return route.path.startsWith('/stocks/')
  }
  return route.path === path
}

const handleMenuClick = (event: Event, path: string): void => {
  if (path === '/ai-analysis' && !isPremium()) {
    event.preventDefault()
    router.push('/premium')
    return
  }

  if (path !== '/logout') {
    return
  }

  event.preventDefault()
  authLogout()
  router.push('/welcome')
}
</script>

