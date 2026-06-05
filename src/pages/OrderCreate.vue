<template>
  <div class="max-w-lg mx-auto">
    <button @click="router.push('/')" class="flex items-center gap-1 text-sky-600 hover:text-sky-800 mb-6 text-sm">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      返回选班
    </button>

    <h1 class="text-2xl font-bold text-sky-900 mb-6">📝 填写学员信息</h1>

    <div v-if="sessionInfo" class="bg-sky-50 rounded-xl p-4 mb-6 text-sm text-sky-800">
      <div class="font-bold mb-1">{{ sessionInfo.title }}</div>
      <div>教练：{{ sessionInfo.coach }} · {{ formatTime(sessionInfo.start_time) }}</div>
      <div class="mt-1 text-orange-600 font-bold">¥{{ (sessionInfo.price / 100).toFixed(2) }}</div>
    </div>

    <form @submit.prevent="submitOrder" class="bg-white rounded-2xl shadow-sm border border-sky-100 p-6 space-y-5">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">学员姓名</label>
        <input v-model="form.student_name" required maxlength="100"
          class="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-sky-300 focus:border-sky-300 outline-none transition" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">学员年龄</label>
        <input v-model.number="form.student_age" type="number" required min="1" max="18"
          class="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-sky-300 focus:border-sky-300 outline-none transition" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">家长姓名</label>
        <input v-model="form.parent_name" required maxlength="100"
          class="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-sky-300 focus:border-sky-300 outline-none transition" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">家长电话</label>
        <input v-model="form.parent_phone" required maxlength="20" type="tel"
          class="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-sky-300 focus:border-sky-300 outline-none transition" />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">优惠券（选填）</label>
        <div class="flex gap-2">
          <input v-model="couponCode" maxlength="50" placeholder="输入优惠码，如 SWIM50"
            @input="resetCoupon"
            class="flex-1 border border-gray-200 rounded-xl px-4 py-2.5 uppercase focus:ring-2 focus:ring-sky-300 focus:border-sky-300 outline-none transition" />
          <button type="button" @click="applyCoupon" :disabled="!couponCode || validatingCoupon"
            class="px-4 rounded-xl bg-sky-100 text-sky-700 hover:bg-sky-200 disabled:opacity-50 transition text-sm font-medium whitespace-nowrap">
            {{ validatingCoupon ? '校验中' : '使用' }}
          </button>
        </div>
        <p v-if="couponMsg" :class="couponValid ? 'text-green-600' : 'text-red-500'" class="text-xs mt-1.5">{{ couponMsg }}</p>
      </div>

      <div v-if="sessionInfo" class="bg-gray-50 rounded-xl p-4 text-sm space-y-1.5">
        <div class="flex justify-between text-gray-600">
          <span>课程原价</span>
          <span>¥{{ (sessionInfo.price / 100).toFixed(2) }}</span>
        </div>
        <div v-if="couponValid && discountAmount > 0" class="flex justify-between text-green-600">
          <span>优惠券抵扣</span>
          <span>- ¥{{ (discountAmount / 100).toFixed(2) }}</span>
        </div>
        <div class="flex justify-between font-bold text-gray-900 pt-1.5 border-t border-gray-200">
          <span>应付金额</span>
          <span class="text-orange-500 text-lg">¥{{ (finalAmount / 100).toFixed(2) }}</span>
        </div>
      </div>

      <div v-if="submitError" class="bg-red-50 text-red-700 rounded-xl p-3 text-sm">{{ submitError }}</div>

      <button type="submit" :disabled="submitting"
        class="w-full py-3 rounded-xl font-medium text-white bg-sky-500 hover:bg-sky-600 disabled:bg-gray-300 transition">
        {{ submitting ? '提交中...' : '确认报名' }}
      </button>

      <p class="text-xs text-gray-400 text-center">下单后 15 分钟内未支付将自动释放名额</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useApi } from '@/composables/useApi'

const router = useRouter()
const route = useRoute()
const { get, post } = useApi()

const sessionId = route.query.sessionId as string

interface SessionInfo {
  title: string
  coach: string
  price: number
  start_time: string
}

interface CouponValidateResult {
  valid: boolean
  code: string
  name?: string
  original_amount: number
  discount_amount: number
  final_amount: number
  message: string
}

const sessionInfo = ref<SessionInfo | null>(null)
const submitting = ref(false)
const submitError = ref<string | null>(null)

const couponCode = ref('')
const couponValid = ref(false)
const couponMsg = ref('')
const validatingCoupon = ref(false)
const discountAmount = ref(0)

const form = reactive({
  student_name: '',
  student_age: 3,
  parent_name: '',
  parent_phone: '',
})

const finalAmount = computed(() => {
  const price = sessionInfo.value?.price || 0
  return couponValid.value ? Math.max(0, price - discountAmount.value) : price
})

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function resetCoupon() {
  couponValid.value = false
  couponMsg.value = ''
  discountAmount.value = 0
}

async function applyCoupon() {
  const code = couponCode.value.trim().toUpperCase()
  couponCode.value = code
  if (!code) return
  validatingCoupon.value = true
  try {
    const res = await post<CouponValidateResult>('/coupons/validate', { code, session_id: sessionId })
    couponValid.value = res.valid
    couponMsg.value = res.valid ? `${res.name}：${res.message}` : res.message
    discountAmount.value = res.discount_amount
  } catch (e: any) {
    couponValid.value = false
    couponMsg.value = e.message || '优惠券校验失败'
    discountAmount.value = 0
  } finally {
    validatingCoupon.value = false
  }
}

onMounted(async () => {
  if (!sessionId) {
    router.push('/')
    return
  }
  try {
    sessionInfo.value = await get<SessionInfo>(`/sessions/${sessionId}`)
  } catch {
    router.push('/')
  }
})

async function submitOrder() {
  submitting.value = true
  submitError.value = null
  try {
    const order = await post<{ id: string }>('/orders', {
      session_id: sessionId,
      ...form,
      coupon_code: couponValid.value ? couponCode.value : null,
    })
    router.push({ name: 'payment', query: { orderId: order.id } })
  } catch (e: any) {
    submitError.value = e.message || '报名失败，请重试'
  } finally {
    submitting.value = false
  }
}
</script>
