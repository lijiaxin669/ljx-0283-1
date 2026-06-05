<template>
  <div class="max-w-lg mx-auto">
    <h1 class="text-2xl font-bold text-sky-900 mb-6">💳 支付确认</h1>

    <div v-if="loading" class="text-center py-16 text-sky-500">加载订单信息...</div>

    <div v-else-if="order" class="space-y-6">
      <div class="bg-white rounded-2xl shadow-sm border border-sky-100 p-6">
        <div class="flex justify-between items-center mb-4">
          <span class="text-sm text-gray-500">订单状态</span>
          <span :class="statusClass" class="px-3 py-1 rounded-full text-sm font-medium">{{ statusLabel }}</span>
        </div>
        <div class="text-3xl font-bold text-orange-500 mb-4">¥{{ (order.amount / 100).toFixed(2) }}</div>
        <div class="text-sm text-gray-500 space-y-1">
          <div>学员：{{ order.student_name }}</div>
          <div>过期时间：{{ formatTime(order.expire_at) }}</div>
        </div>

        <div v-if="order.status === 'pending'" class="mt-4">
          <div class="text-xs text-gray-400 mb-3">倒计时：<span class="text-red-500 font-mono">{{ countdown }}</span></div>
        </div>
      </div>

      <div v-if="order.status === 'pending' && !paymentCreated" class="space-y-3">
        <div class="bg-white rounded-2xl shadow-sm border border-sky-100 p-6">
          <label class="block text-sm font-medium text-gray-700 mb-3">选择支付方式</label>
          <div class="grid grid-cols-2 gap-3">
            <button @click="channel = 'wechat'" :class="channel === 'wechat' ? 'border-green-500 bg-green-50' : 'border-gray-200'"
              class="border-2 rounded-xl p-3 text-center transition">
              <div class="text-2xl mb-1">💚</div>
              <div class="text-sm font-medium">微信支付</div>
            </button>
            <button @click="channel = 'alipay'" :class="channel === 'alipay' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'"
              class="border-2 rounded-xl p-3 text-center transition">
              <div class="text-2xl mb-1">💙</div>
              <div class="text-sm font-medium">支付宝</div>
            </button>
          </div>
        </div>
        <button @click="createPayment" :disabled="!channel || creatingPayment"
          class="w-full py-3 rounded-xl font-medium text-white bg-sky-500 hover:bg-sky-600 disabled:bg-gray-300 transition">
          {{ creatingPayment ? '创建支付...' : '发起支付' }}
        </button>
      </div>

      <div v-if="paymentCreated" class="bg-white rounded-2xl shadow-sm border border-sky-100 p-6 text-center">
        <div class="text-4xl mb-3">⏳</div>
        <p class="text-gray-600 mb-4">支付创建成功，请完成支付</p>
        <p class="text-xs text-gray-400 mb-4">支付单号：{{ paymentId }}</p>
        <button @click="simulateCallback"
          class="px-6 py-2 rounded-xl bg-orange-500 text-white hover:bg-orange-600 transition text-sm">
          模拟支付回调（测试用）
        </button>
      </div>

      <div v-if="order.status === 'paid'" class="text-center">
        <div class="text-4xl mb-3">✅</div>
        <p class="text-green-600 font-bold text-lg mb-4">支付成功！</p>
        <router-link :to="{ name: 'voucher', query: { orderId: order.id } }"
          class="inline-block px-6 py-3 rounded-xl bg-sky-500 text-white hover:bg-sky-600 transition font-medium">
          查看电子凭证
        </router-link>
      </div>

      <div v-if="order.status === 'expired'" class="text-center">
        <div class="text-4xl mb-3">⏰</div>
        <p class="text-red-500 font-bold text-lg mb-4">订单已过期，名额已释放</p>
        <router-link to="/" class="inline-block px-6 py-3 rounded-xl bg-sky-500 text-white hover:bg-sky-600 transition font-medium">
          重新选班
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '@/composables/useApi'

const route = useRoute()
const router = useRouter()
const { loading, error, get, post } = useApi()

const orderId = route.query.orderId as string

interface OrderInfo {
  id: string
  status: string
  amount: number
  student_name: string
  expire_at: string
}

const order = ref<OrderInfo | null>(null)
const channel = ref('wechat')
const paymentCreated = ref(false)
const paymentId = ref('')
const creatingPayment = ref(false)
const countdown = ref('')
let timer: ReturnType<typeof setInterval> | null = null

const statusLabel = computed(() => {
  const m: Record<string, string> = { pending: '待支付', paid: '已支付', expired: '已过期', cancelled: '已取消' }
  return m[order.value?.status || ''] || order.value?.status || ''
})

const statusClass = computed(() => {
  const m: Record<string, string> = { pending: 'bg-yellow-100 text-yellow-700', paid: 'bg-green-100 text-green-700', expired: 'bg-red-100 text-red-700' }
  return m[order.value?.status || ''] || 'bg-gray-100 text-gray-600'
})

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN')
}

function updateCountdown() {
  if (!order.value || order.value.status !== 'pending') return
  const diff = new Date(order.value.expire_at).getTime() - Date.now()
  if (diff <= 0) {
    countdown.value = '已过期'
    return
  }
  const m = Math.floor(diff / 60000)
  const s = Math.floor((diff % 60000) / 1000)
  countdown.value = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

async function refreshOrder() {
  try {
    order.value = await get<OrderInfo>(`/orders/${orderId}`)
    if (order.value?.status === 'paid') {
      if (timer) { clearInterval(timer); timer = null }
    }
  } catch {}
}

async function createPayment() {
  creatingPayment.value = true
  try {
    const res = await post<{ payment_id: string }>('/payments/create', {
      order_id: orderId,
      channel: channel.value,
    })
    paymentId.value = res.payment_id
    paymentCreated.value = true
  } catch (e: any) {
    alert(e.message || '创建支付失败')
  } finally {
    creatingPayment.value = false
  }
}

async function simulateCallback() {
  try {
    await post('/payments/callback', {
      payment_id: paymentId.value,
      order_id: orderId,
      channel: channel.value,
      amount: order.value?.amount,
      status: 'paid',
    })
    await refreshOrder()
  } catch (e: any) {
    alert(e.message || '回调失败')
  }
}

onMounted(async () => {
  if (!orderId) { router.push('/'); return }
  await refreshOrder()
  timer = setInterval(async () => {
    updateCountdown()
    if (order.value?.status === 'pending') {
      await refreshOrder()
    }
  }, 5000)
  updateCountdown()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
