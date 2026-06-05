<template>
  <div class="max-w-lg mx-auto">
    <div v-if="loading" class="text-center py-16 text-sky-500">加载凭证...</div>

    <div v-else-if="voucher" class="space-y-6">
      <div class="text-center mb-2">
        <div class="text-4xl mb-2">🎉</div>
        <h1 class="text-2xl font-bold text-sky-900">报名成功 - 电子凭证</h1>
      </div>

      <div class="bg-white rounded-2xl shadow-lg border-2 border-sky-200 overflow-hidden">
        <div class="bg-gradient-to-r from-sky-500 to-cyan-500 p-6 text-white text-center">
          <div class="text-3xl font-bold mb-1">少年宫亲子游泳班</div>
          <div class="text-sky-100">入場凭证</div>
        </div>

        <div class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div class="text-gray-400 mb-1">学员姓名</div>
              <div class="font-bold text-gray-900">{{ voucher.student_name }}</div>
            </div>
            <div>
              <div class="text-gray-400 mb-1">学员年龄</div>
              <div class="font-bold text-gray-900">{{ voucher.student_age }} 岁</div>
            </div>
            <div>
              <div class="text-gray-400 mb-1">家长姓名</div>
              <div class="font-bold text-gray-900">{{ voucher.parent_name }}</div>
            </div>
            <div>
              <div class="text-gray-400 mb-1">家长电话</div>
              <div class="font-bold text-gray-900">{{ voucher.parent_phone }}</div>
            </div>
          </div>

          <hr class="border-dashed border-gray-200" />

          <div class="space-y-2 text-sm">
            <div>
              <span class="text-gray-400">场次：</span>
              <span class="font-bold text-gray-900">{{ voucher.session_title }}</span>
            </div>
            <div>
              <span class="text-gray-400">教练：</span>
              <span class="font-bold text-gray-900">{{ voucher.coach }}</span>
            </div>
            <div>
              <span class="text-gray-400">时间：</span>
              <span class="font-bold text-gray-900">{{ formatTime(voucher.start_time) }} — {{ formatTime(voucher.end_time) }}</span>
            </div>
          </div>

          <hr class="border-dashed border-gray-200" />

          <div class="flex justify-between items-end">
            <div>
              <div class="text-gray-400 text-xs">支付金额</div>
              <div class="text-2xl font-bold text-orange-500">¥{{ (voucher.amount / 100).toFixed(2) }}</div>
            </div>
            <div class="text-right text-xs text-gray-400">
              <div>支付单号：{{ voucher.payment_id }}</div>
              <div>支付时间：{{ formatTime(voucher.paid_at) }}</div>
            </div>
          </div>
        </div>

        <div class="border-t-2 border-dashed border-gray-200 px-6 py-4 bg-gray-50 text-center text-xs text-gray-400">
          请凭此凭证入场 · 订单号 {{ voucher.order_id }}
        </div>
      </div>

      <div class="text-center">
        <router-link to="/" class="text-sky-600 hover:text-sky-800 text-sm">返回首页</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'

const route = useRoute()
const router = useRouter()
const { loading, get } = useApi()

const orderId = route.query.orderId as string

interface Voucher {
  order_id: string
  student_name: string
  student_age: number
  parent_name: string
  parent_phone: string
  session_title: string
  coach: string
  start_time: string
  end_time: string
  amount: number
  payment_id: string
  paid_at: string
}

const voucher = ref<Voucher | null>(null)

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  if (!orderId) { router.push('/'); return }
  try {
    voucher.value = await get<Voucher>(`/orders/${orderId}/voucher`)
  } catch {
    router.push('/')
  }
})
</script>
