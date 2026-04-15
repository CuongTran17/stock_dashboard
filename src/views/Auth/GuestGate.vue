<template>
  <main class="relative h-screen w-screen overflow-hidden bg-brand-950">
    <video
      class="absolute inset-0 h-full w-full object-cover"
      autoplay
      muted
      loop
      playsinline
      preload="auto"
    >
      <source src="https://cdn.coverr.co/videos/coverr-stocks-on-monitor-1579/1080p.mp4" type="video/mp4" />
    </video>

    <div class="absolute inset-0 bg-gradient-to-b from-brand-950/70 via-brand-950/50 to-gray-950/80"></div>

    <div class="relative z-10 flex h-full flex-col items-center justify-center px-6 text-center">
      <p class="mb-4 text-xs font-semibold uppercase tracking-[0.28em] text-brand-100/80">The Fin1</p>
      <h1 class="max-w-4xl text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl">
        JOIN WITH US
      </h1>
      <p class="mt-4 max-w-2xl text-sm text-brand-100/90 sm:text-base">
        Nền tảng phân tích chứng khoán realtime dành cho nhà đầu tư hiện đại.
      </p>

      <button
        class="mt-10 rounded-2xl border border-brand-200/70 bg-brand-500/90 px-10 py-4 text-base font-semibold tracking-wide text-white shadow-xl shadow-brand-900/40 transition hover:scale-[1.02] hover:bg-brand-500"
        @click="goToSignin"
      >
        JOIN WITH US
      </button>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goToSignin = () => {
  router.push('/signin')
}
</script>
