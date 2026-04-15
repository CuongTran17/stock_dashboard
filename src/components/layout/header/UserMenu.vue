<template>
  <div class="relative" ref="dropdownRef">
    <button
      class="flex items-center text-gray-700 dark:text-gray-400"
      @click.prevent="toggleDropdown"
    >
      <span class="mr-3 overflow-hidden rounded-full h-11 w-11">
        <img src="/images/user/owner.jpg" alt="User" />
      </span>

      <span class="block mr-1 font-medium text-theme-sm">{{ displayName }}</span>

      <ChevronDownIcon :class="{ 'rotate-180': dropdownOpen }" />
    </button>

    <!-- Dropdown Start -->
    <div
      v-if="dropdownOpen"
      class="absolute right-0 mt-[17px] flex w-[260px] flex-col rounded-2xl border border-gray-200 bg-white p-3 shadow-theme-lg dark:border-gray-800 dark:bg-gray-dark"
    >
      <div>
        <span class="block font-medium text-gray-700 text-theme-sm dark:text-gray-400">
          {{ displayName }}
        </span>
        <span class="mt-0.5 block text-theme-xs text-gray-500 dark:text-gray-400">
          {{ displayEmail }}
        </span>
      </div>

      <ul class="flex flex-col gap-1 pt-4 pb-3 border-b border-gray-200 dark:border-gray-800">
        <li v-for="item in menuItems" :key="item.href">
          <router-link
            :to="item.href"
            class="flex items-center gap-3 px-3 py-2 font-medium text-gray-700 rounded-lg group text-theme-sm hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-white/5 dark:hover:text-gray-300"
          >
            <!-- SVG icon would go here -->
            <component
              :is="item.icon"
              class="text-gray-500 group-hover:text-gray-700 dark:group-hover:text-gray-300"
            />
            {{ item.text }}
          </router-link>
        </li>
      </ul>
      <router-link
        to="/signin"
        @click="signOut"
        class="flex items-center gap-3 px-3 py-2 mt-3 font-medium text-gray-700 rounded-lg group text-theme-sm hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-white/5 dark:hover:text-gray-300"
      >
        <LogoutIcon
          class="text-gray-500 group-hover:text-gray-700 dark:group-hover:text-gray-300"
        />
        Đăng xuất
      </router-link>
    </div>
    <!-- Dropdown End -->
  </div>
</template>

<script setup lang="ts">
import { ChevronDownIcon, InfoCircleIcon, LogoutIcon, SettingsIcon, UserCircleIcon } from '@/icons'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getSavedUser, isLoggedIn, logout as authLogout } from '@/services/authApi'

const router = useRouter()
const dropdownOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const currentUser = computed(() => getSavedUser())
const displayName = computed(() => currentUser.value?.fullname || 'Khách')
const displayEmail = computed(() => currentUser.value?.email || '')
const loggedIn = computed(() => isLoggedIn())

const menuItems = [
  { href: '/my-portfolio', icon: UserCircleIcon, text: 'Danh mục của tôi' },
  { href: '/screener', icon: SettingsIcon, text: 'Lọc cổ phiếu' },
  { href: '/news-events', icon: InfoCircleIcon, text: 'Tin tức thị trường' },
]

const toggleDropdown = () => {
  dropdownOpen.value = !dropdownOpen.value
}

const closeDropdown = () => {
  dropdownOpen.value = false
}

const signOut = () => {
  authLogout()
  closeDropdown()
  router.push('/signin')
}

const handleClickOutside = (event: Event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
