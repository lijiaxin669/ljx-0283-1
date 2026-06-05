<template>
  <div>
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-sky-900 mb-2">🔧 管理端</h1>
      <p class="text-sky-600">订单管理、数据统计与导出</p>
    </div>

    <div v-if="!authenticated" class="max-w-sm mx-auto">
      <div class="bg-white rounded-2xl shadow-sm border border-sky-100 p-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">管理端登录</h2>
        <div class="space-y-4">
          <input v-model="adminSecret" type="password" placeholder="请输入管理密钥"
            class="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-sky-300 outline-none" />
          <button @click="login" class="w-full py-2.5 rounded-xl bg-sky-500 text-white hover:bg-sky-600 transition font-medium">
            登录
          </button>
        </div>
      </div>
    </div>

    <div v-else class="space-y-6">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div v-for="s in statCards" :key="s.label" class="bg-white rounded-xl shadow-sm border border-sky-100 p-4">
          <div class="text-sm text-gray-500">{{ s.label }}</div>
          <div class="text-2xl font-bold" :class="s.color">{{ s.value }}</div>
        </div>
      </div>

      <div class="flex gap-3">
        <button @click="exportCsv" class="px-4 py-2 rounded-xl bg-sky-500 text-white hover:bg-sky-600 transition text-sm font-medium">
          📥 导出 CSV
        </button>
        <select v-model="filterStatus" @change="loadOrders" class="border border-gray-200 rounded-xl px-3 py-2 text-sm">
          <option value="">全部状态</option>
          <option value="pending">待支付</option>
          <option value="paid">已支付</option>
          <option value="expired">已过期</option>
        </select>
      </div>

      <div class="bg-white rounded-2xl shadow-sm border border-sky-100 overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-sky-50 text-sky-800">
            <tr>
              <th class="px-4 py-3 text-left">学员</th>
              <th class="px-4 py-3 text-left">家长</th>
              <th class="px-4 py-3 text-left">电话</th>
              <th class="px-4 py-3 text-left">金额</th>
              <th class="px-4 py-3 text-left">状态</th>
              <th class="px-4 py-3 text-left">创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in orders" :key="o.id" class="border-t border-gray-50 hover:bg-gray-50">
              <td class="px-4 py-3">{{ o.student_name }} ({{ o.student_age }}岁)</td>
              <td class="px-4 py-3">{{ o.parent_name }}</td>
              <td class="px-4 py-3">{{ o.parent_phone }}</td>
              <td class="px-4 py-3">¥{{ (o.amount / 100).toFixed(2) }}</td>
              <td class="px-4 py-3">
                <span :class="orderStatusClass(o.status)" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ orderStatusLabel(o.status) }}</span>
              </td>
              <td class="px-4 py-3 text-gray-400">{{ new Date(o.created_at).toLocaleString('zh-CN') }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="orders.length === 0" class="text-center py-8 text-gray-400">暂无订单</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useApi } from '@/composables/useApi'

const { get, download } = useApi()
const adminSecret = ref('')
const authenticated = ref(false)
const filterStatus = ref('')
const stats = ref({ total_orders: 0, paid_orders: 0, pending_orders: 0, expired_orders: 0, total_revenue: 0 })

interface OrderRow {
  id: string
  student_name: string
  student_age: number
  parent_name: string
  parent_phone: string
  amount: number
  status: string
  created_at: string
}

const orders = ref<OrderRow[]>([])

const statCards = computed(() => [
  { label: '总订单', value: stats.value.total_orders, color: 'text-sky-600' },
  { label: '已支付', value: stats.value.paid_orders, color: 'text-green-600' },
  { label: '待支付', value: stats.value.pending_orders, color: 'text-yellow-600' },
  { label: '总收入', value: `¥${(stats.value.total_revenue / 100).toFixed(2)}`, color: 'text-orange-600' },
])

function orderStatusLabel(s: string) {
  const m: Record<string, string> = { pending: '待支付', paid: '已支付', expired: '已过期', cancelled: '已取消' }
  return m[s] || s
}

function orderStatusClass(s: string) {
  const m: Record<string, string> = { pending: 'bg-yellow-100 text-yellow-700', paid: 'bg-green-100 text-green-700', expired: 'bg-red-100 text-red-700' }
  return m[s] || 'bg-gray-100 text-gray-600'
}

function login() {
  if (adminSecret.value.trim()) {
    authenticated.value = true
    loadStats()
    loadOrders()
  }
}

async function loadStats() {
  try {
    stats.value = await get('/admin/stats')
  } catch {}
}

async function loadOrders() {
  try {
    const path = filterStatus.value ? `/admin/orders?status=${filterStatus.value}` : '/admin/orders'
    orders.value = await get<OrderRow[]>(path)
  } catch {}
}

async function exportCsv() {
  try {
    await download('/admin/orders/export', 'orders.csv', { 'X-Admin-Secret': adminSecret.value })
  } catch (e: any) {
    alert(e.message || '导出失败')
  }
}
</script>
