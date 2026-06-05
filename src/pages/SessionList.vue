<template>
  <div>
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-sky-900 mb-2">🏊 选择游泳场次</h1>
      <p class="text-sky-600">为孩子挑选合适的亲子游泳班，名额有限先到先得</p>
    </div>

    <div v-if="loading" class="text-center py-16 text-sky-500">加载中...</div>

    <div v-else-if="error" class="bg-red-50 text-red-700 rounded-xl p-6">{{ error }}</div>

    <div v-else class="grid md:grid-cols-2 gap-6">
      <div
        v-for="s in sessions"
        :key="s.id"
        class="bg-white rounded-2xl shadow-sm border border-sky-100 p-6 hover:shadow-md transition-shadow"
      >
        <div class="flex justify-between items-start mb-4">
          <h3 class="text-lg font-bold text-sky-900">{{ s.title }}</h3>
          <span
            :class="s.status === 'open' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
            class="text-xs px-2 py-1 rounded-full font-medium"
          >{{ s.status === 'open' ? '可报名' : '已满' }}</span>
        </div>
        <p v-if="s.description" class="text-sm text-gray-500 mb-3">{{ s.description }}</p>
        <div class="space-y-2 text-sm text-gray-600">
          <div class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
            教练：{{ s.coach }}
          </div>
          <div class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            {{ formatTime(s.start_time) }} — {{ formatTime(s.end_time) }}
          </div>
          <div class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            余位：<span :class="s.available_slots <= 3 ? 'text-red-500 font-bold' : 'text-green-600 font-bold'">{{ s.available_slots }}</span> / {{ s.total_slots }}
          </div>
          <div class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <span class="text-xl font-bold text-orange-500">¥{{ (s.price / 100).toFixed(2) }}</span>
          </div>
        </div>
        <button
          :disabled="s.status !== 'open' || s.available_slots <= 0"
          @click="selectSession(s)"
          class="mt-4 w-full py-2.5 rounded-xl font-medium transition disabled:bg-gray-100 disabled:text-gray-400"
          :class="s.status === 'open' && s.available_slots > 0 ? 'bg-sky-500 text-white hover:bg-sky-600' : 'bg-gray-100 text-gray-400'"
        >{{ s.status === 'open' && s.available_slots > 0 ? '立即报名' : '已满员' }}</button>
      </div>
    </div>

    <div v-if="!loading && !error && sessions.length === 0" class="text-center py-16 text-gray-400">
      暂无可用场次
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'

const router = useRouter()
const { loading, error, get } = useApi()

interface Session {
  id: string
  title: string
  description: string | null
  coach: string
  start_time: string
  end_time: string
  total_slots: number
  available_slots: number
  price: number
  status: string
}

const sessions = ref<Session[]>([])

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function selectSession(s: Session) {
  router.push({ name: 'order', query: { sessionId: s.id } })
}

onMounted(async () => {
  try {
    sessions.value = await get<Session[]>('/sessions')
  } catch {}
})
</script>
