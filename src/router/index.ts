import { createRouter, createWebHistory } from 'vue-router'
import SessionList from '@/pages/SessionList.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: SessionList,
  },
  {
    path: '/order',
    name: 'order',
    component: () => import('@/pages/OrderCreate.vue'),
  },
  {
    path: '/payment',
    name: 'payment',
    component: () => import('@/pages/PaymentPage.vue'),
  },
  {
    path: '/voucher',
    name: 'voucher',
    component: () => import('@/pages/VoucherPage.vue'),
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/pages/AdminPage.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
