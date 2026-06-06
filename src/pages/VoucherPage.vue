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
          <div class="flex justify-center py-2">
            <div class="bg-white p-3 rounded-xl border border-gray-100">
              <canvas ref="qrcodeCanvas" class="w-40 h-40"></canvas>
            </div>
          </div>

          <div class="text-center">
            <div class="text-xs text-gray-400 mb-1">核销码</div>
            <div class="font-mono text-2xl font-bold tracking-wider text-sky-700">{{ voucher.checkin_code }}</div>
          </div>

          <div class="text-center">
            <span :class="checkinStatusClass(voucher.checkin_status)" class="px-4 py-1.5 rounded-full text-sm font-medium">
              {{ checkinStatusLabel(voucher.checkin_status) }}
            </span>
            <div v-if="voucher.checked_in_at" class="text-xs text-gray-400 mt-2">
              签到时间：{{ formatTime(voucher.checked_in_at) }}
            </div>
          </div>

          <hr class="border-dashed border-gray-200" />

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
              <div v-if="voucher.discount_amount > 0" class="text-xs text-green-600 mt-0.5">
                优惠券 {{ voucher.coupon_code }} 已省 ¥{{ (voucher.discount_amount / 100).toFixed(2) }}
              </div>
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
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'
import QRCode from 'qrcode'

const route = useRoute()
const router = useRouter()
const { loading, get } = useApi()

const orderId = route.query.orderId as string
const qrcodeCanvas = ref<HTMLCanvasElement | null>(null)

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
  original_amount: number
  discount_amount: number
  coupon_code: string | null
  payment_id: string
  paid_at: string
  checkin_code: string
  checkin_status: string
  checked_in_at: string | null
}

const voucher = ref<Voucher | null>(null)

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function checkinStatusLabel(s: string) {
  const m: Record<string, string> = { pending: '待签到', checked_in: '已签到' }
  return m[s] || s
}

function checkinStatusClass(s: string) {
  const m: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    checked_in: 'bg-green-100 text-green-700'
  }
  return m[s] || 'bg-gray-100 text-gray-600'
}

async function generateQRCode() {
  if (!voucher.value || !qrcodeCanvas.value) return
  const qrContent = JSON.stringify({
    order_id: voucher.value.order_id,
    checkin_code: voucher.value.checkin_code,
  })
  try {
    await QRCode.toCanvas(qrcodeCanvas.value, qrContent, {
      width: 160,
      margin: 1,
      color: { dark: '#0c4a6e', light: '#ffffff' },
    })
  } catch (e) {
    console.error('QRCode generate error:', e)
  }
}

watch(voucher, () => {
  nextTick(() => generateQRCode())
})

onMounted(async () => {
  if (!orderId) { router.push('/'); return }
  try {
    voucher.value = await get<Voucher>(`/orders/${orderId}/voucher`)
  } catch {
    router.push('/')
  }
})
</script>
