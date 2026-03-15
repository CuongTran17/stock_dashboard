<template>
  <div class="flex items-center gap-2">
    <div
      :class="[
        'w-2 h-2 rounded-full',
        connected ? 'bg-success-500 animate-pulse' : 'bg-gray-400',
      ]"
    ></div>
    <span class="text-xs text-gray-500 dark:text-gray-400">
      {{ connected ? 'Live' : 'Offline' }}
    </span>
    <span v-if="lastUpdate" class="text-xs text-gray-400 dark:text-gray-500">
      {{ formatTime(lastUpdate) }}
    </span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  connected: boolean
  lastUpdate?: Date
}>()

function formatTime(date: Date): string {
  return date.toLocaleTimeString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
</script>
