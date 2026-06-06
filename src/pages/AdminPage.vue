<template>
  <div>
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-sky-900 mb-2">🔧 管理端</h1>
      <p class="text-sky-600">订单管理、优惠券、退款审批与数据统计</p>
    </div>

    <div v-if="!authenticated" class="max-w-sm mx-auto">
      <div class="bg-white rounded-2xl shadow-sm border border-sky-100 p-6">
        <h2 class="text-lg font-bold text-gray-900 mb-4">管理端登录</h2>
        <div class="space-y-4">
          <input v-model="adminSecret" type="password" placeholder="请输入管理密钥（默认 changeme）"
            class="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-sky-300 outline-none"
            @keyup.enter="login" />
          <button @click="login" class="w-full py-2.5 rounded-xl bg-sky-500 text-white hover:bg-sky-600 transition font-medium">
            登录
          </button>
          <p v-if="loginError" class="text-red-500 text-sm">{{ loginError }}</p>
        </div>
      </div>
    </div>

    <div v-else class="space-y-6">
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <div v-for="s in statCards" :key="s.label" class="bg-white rounded-xl shadow-sm border border-sky-100 p-4">
          <div class="text-sm text-gray-500">{{ s.label }}</div>
          <div class="text-2xl font-bold" :class="s.color">{{ s.value }}</div>
        </div>
      </div>

      <div class="flex gap-2 border-b border-gray-200">
        <button v-for="t in tabs" :key="t.key" @click="switchTab(t.key)"
          :class="activeTab === t.key ? 'border-sky-500 text-sky-700' : 'border-transparent text-gray-500 hover:text-gray-700'"
          class="px-4 py-2 -mb-px border-b-2 font-medium text-sm transition flex items-center gap-1">
          {{ t.label }}
          <span v-if="t.key === 'refunds' && stats.pending_refunds > 0"
            class="bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 leading-none">{{ stats.pending_refunds }}</span>
        </button>
      </div>

      <!-- 订单 -->
      <div v-show="activeTab === 'orders'" class="space-y-4">
        <div class="flex gap-3 items-center flex-wrap">
          <button @click="exportCsv" :disabled="exporting"
            class="px-4 py-2 rounded-xl bg-sky-500 text-white hover:bg-sky-600 transition text-sm font-medium disabled:bg-gray-300">
            {{ exporting ? '导出中...' : '📥 导出 CSV' }}
          </button>
          <select v-model="filterStatus" @change="loadOrders" class="border border-gray-200 rounded-xl px-3 py-2 text-sm">
            <option value="">全部状态</option>
            <option value="pending">待支付</option>
            <option value="paid">已支付</option>
            <option value="expired">已过期</option>
            <option value="refunding">退款审核中</option>
            <option value="refunded">已退款</option>
          </select>
          <button @click="loadStats(); loadOrders()" class="px-4 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 transition text-sm">
            🔄 刷新
          </button>
        </div>

        <div class="bg-white rounded-2xl shadow-sm border border-sky-100 overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-sky-50 text-sky-800">
              <tr>
                <th class="px-4 py-3 text-left">学员</th>
                <th class="px-4 py-3 text-left">家长</th>
                <th class="px-4 py-3 text-left">电话</th>
                <th class="px-4 py-3 text-left">优惠券</th>
                <th class="px-4 py-3 text-left">实付</th>
                <th class="px-4 py-3 text-left">状态</th>
                <th class="px-4 py-3 text-left">创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="o in orders" :key="o.id" class="border-t border-gray-50 hover:bg-gray-50">
                <td class="px-4 py-3">{{ o.student_name }} ({{ o.student_age }}岁)</td>
                <td class="px-4 py-3">{{ o.parent_name }}</td>
                <td class="px-4 py-3">{{ o.parent_phone }}</td>
                <td class="px-4 py-3">
                  <span v-if="o.coupon_code" class="text-green-600 text-xs">{{ o.coupon_code }} (-¥{{ (o.discount_amount / 100).toFixed(2) }})</span>
                  <span v-else class="text-gray-300">—</span>
                </td>
                <td class="px-4 py-3 font-medium">¥{{ (o.amount / 100).toFixed(2) }}</td>
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

      <!-- 优惠券 -->
      <div v-show="activeTab === 'coupons'" class="space-y-4">
        <div class="flex justify-between items-center">
          <button @click="showCouponForm = !showCouponForm"
            class="px-4 py-2 rounded-xl bg-sky-500 text-white hover:bg-sky-600 transition text-sm font-medium">
            {{ showCouponForm ? '收起' : '＋ 新建优惠券' }}
          </button>
          <button @click="loadCoupons" class="px-4 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 transition text-sm">🔄 刷新</button>
        </div>

        <div v-if="showCouponForm" class="bg-white rounded-2xl shadow-sm border border-sky-100 p-6">
          <div class="grid md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-gray-500 mb-1">优惠码</label>
              <input v-model="couponForm.code" placeholder="如 SWIM50" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm uppercase outline-none focus:ring-2 focus:ring-sky-300" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">名称</label>
              <input v-model="couponForm.name" placeholder="如 新生立减券" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">类型</label>
              <select v-model="couponForm.discount_type" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
                <option value="fixed">固定立减（元）</option>
                <option value="percent">百分比立减（%）</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">{{ couponForm.discount_type === 'fixed' ? '立减金额（元）' : '立减比例（%）' }}</label>
              <input v-model.number="couponForm.discount_value" type="number" min="1" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">使用门槛（元，0 为无门槛）</label>
              <input v-model.number="couponForm.min_amount" type="number" min="0" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
            </div>
            <div v-if="couponForm.discount_type === 'percent'">
              <label class="block text-xs text-gray-500 mb-1">最高优惠（元，0 为不限）</label>
              <input v-model.number="couponForm.max_discount" type="number" min="0" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">发放数量</label>
              <input v-model.number="couponForm.total_quantity" type="number" min="1" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">生效时间</label>
              <input v-model="couponForm.valid_from" type="datetime-local" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">失效时间</label>
              <input v-model="couponForm.valid_until" type="datetime-local" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
            </div>
          </div>
          <p v-if="couponError" class="text-red-500 text-sm mt-3">{{ couponError }}</p>
          <button @click="createCoupon" :disabled="creatingCoupon"
            class="mt-4 px-6 py-2.5 rounded-xl bg-sky-500 text-white hover:bg-sky-600 disabled:bg-gray-300 transition text-sm font-medium">
            {{ creatingCoupon ? '创建中...' : '创建优惠券' }}
          </button>
        </div>

        <div class="bg-white rounded-2xl shadow-sm border border-sky-100 overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-sky-50 text-sky-800">
              <tr>
                <th class="px-4 py-3 text-left">优惠码</th>
                <th class="px-4 py-3 text-left">名称</th>
                <th class="px-4 py-3 text-left">优惠</th>
                <th class="px-4 py-3 text-left">门槛</th>
                <th class="px-4 py-3 text-left">已用/总量</th>
                <th class="px-4 py-3 text-left">有效期</th>
                <th class="px-4 py-3 text-left">状态</th>
                <th class="px-4 py-3 text-left">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in coupons" :key="c.id" class="border-t border-gray-50 hover:bg-gray-50">
                <td class="px-4 py-3 font-mono font-medium">{{ c.code }}</td>
                <td class="px-4 py-3">{{ c.name }}</td>
                <td class="px-4 py-3">{{ couponDiscountText(c) }}</td>
                <td class="px-4 py-3">{{ c.min_amount > 0 ? `满¥${(c.min_amount / 100).toFixed(0)}` : '无' }}</td>
                <td class="px-4 py-3">{{ c.used_quantity }} / {{ c.total_quantity }}</td>
                <td class="px-4 py-3 text-gray-400 text-xs">{{ formatDate(c.valid_from) }} ~ {{ formatDate(c.valid_until) }}</td>
                <td class="px-4 py-3">
                  <span :class="c.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'" class="px-2 py-0.5 rounded-full text-xs font-medium">
                    {{ c.status === 'active' ? '启用' : '停用' }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <button @click="toggleCoupon(c)" class="text-sky-600 hover:text-sky-800 text-xs font-medium">
                    {{ c.status === 'active' ? '停用' : '启用' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="coupons.length === 0" class="text-center py-8 text-gray-400">暂无优惠券</div>
        </div>
      </div>

      <!-- 场次管理 -->
      <div v-show="activeTab === 'sessions'" class="space-y-4">
        <div class="flex gap-3 items-center flex-wrap">
          <button @click="openCreateSession"
            class="px-4 py-2 rounded-xl bg-sky-500 text-white hover:bg-sky-600 transition text-sm font-medium">
            ＋ 新建场次
          </button>
          <button @click="loadSessions" class="px-4 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 transition text-sm">🔄 刷新</button>
        </div>

        <div class="bg-white rounded-2xl shadow-sm border border-sky-100 overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-sky-50 text-sky-800">
              <tr>
                <th class="px-4 py-3 text-left">场次</th>
                <th class="px-4 py-3 text-left">教练</th>
                <th class="px-4 py-3 text-left">时间</th>
                <th class="px-4 py-3 text-left">价格</th>
                <th class="px-4 py-3 text-left">名额</th>
                <th class="px-4 py-3 text-left">状态</th>
                <th class="px-4 py-3 text-left">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in sessions" :key="s.id" class="border-t border-gray-50 hover:bg-gray-50">
                <td class="px-4 py-3">
                  <div class="font-medium text-sky-900">{{ s.title }}</div>
                  <div v-if="s.description" class="text-xs text-gray-400 mt-0.5 max-w-xs truncate">{{ s.description }}</div>
                </td>
                <td class="px-4 py-3">{{ s.coach }}</td>
                <td class="px-4 py-3 text-gray-600 text-xs">
                  <div>{{ new Date(s.start_time).toLocaleString('zh-CN') }}</div>
                  <div class="text-gray-400">至 {{ new Date(s.end_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}</div>
                </td>
                <td class="px-4 py-3 font-medium text-orange-500">¥{{ (s.price / 100).toFixed(2) }}</td>
                <td class="px-4 py-3">
                  <span :class="s.available_slots <= 3 ? 'text-red-500' : 'text-green-600'" class="font-bold">{{ s.available_slots }}</span>
                  <span class="text-gray-400"> / {{ s.total_slots }}</span>
                </td>
                <td class="px-4 py-3">
                  <span :class="sessionStatusClass(s.status)" class="px-2 py-0.5 rounded-full text-xs font-medium">
                    {{ sessionStatusLabel(s.status) }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <div class="flex gap-2 flex-wrap">
                    <button @click="openSessionDetail(s)" class="text-sky-600 hover:text-sky-800 text-xs font-medium">详情</button>
                    <button @click="openEditSession(s)" class="text-sky-600 hover:text-sky-800 text-xs font-medium">编辑</button>
                    <button @click="openSlotsEditor(s)" class="text-amber-600 hover:text-amber-800 text-xs font-medium">名额</button>
                    <button @click="openCheckinRoster(s)" class="text-emerald-600 hover:text-emerald-800 text-xs font-medium">签到</button>
                    <button @click="toggleSessionStatus(s)" :disabled="processingSession === s.id"
                      class="text-xs font-medium disabled:opacity-50"
                      :class="s.status === 'open' ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'">
                      {{ s.status === 'open' ? '关闭' : '开启' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="sessions.length === 0" class="text-center py-8 text-gray-400">暂无场次</div>
        </div>

        <!-- 新建/编辑场次弹窗 -->
        <div v-if="showSessionForm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div class="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
              <h3 class="text-lg font-bold text-sky-900">{{ editingSession ? '编辑场次' : '新建场次' }}</h3>
              <button @click="showSessionForm = false" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div class="p-6 space-y-4">
              <div>
                <label class="block text-xs text-gray-500 mb-1">场次标题 *</label>
                <input v-model="sessionForm.title" placeholder="如 亲子游泳启蒙班" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">描述</label>
                <textarea v-model="sessionForm.description" placeholder="可包含适合年龄等信息，如「适合 1-3 岁宝宝」" rows="3" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">教练 *</label>
                <input v-model="sessionForm.coach" placeholder="如 李教练" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">开始时间 *</label>
                  <input v-model="sessionForm.start_time" type="datetime-local" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">结束时间 *</label>
                  <input v-model="sessionForm.end_time" type="datetime-local" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">总名额</label>
                  <input v-model.number="sessionForm.total_slots" type="number" min="1" :disabled="!!editingSession" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300 disabled:bg-gray-50 disabled:text-gray-400" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">价格（元）</label>
                  <input v-model.number="sessionForm.price" type="number" min="1" step="0.01" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
                </div>
              </div>
              <p v-if="sessionError" class="text-red-500 text-sm">{{ sessionError }}</p>
            </div>
            <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <button @click="showSessionForm = false" class="px-4 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 text-sm">取消</button>
              <button @click="saveSession" :disabled="creatingSession"
                class="px-4 py-2 rounded-xl bg-sky-500 text-white hover:bg-sky-600 disabled:bg-gray-300 text-sm font-medium">
                {{ creatingSession ? '保存中...' : '保存' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 调整名额弹窗 -->
        <div v-if="editingSlots" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div class="bg-white rounded-2xl shadow-xl max-w-sm w-full">
            <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
              <h3 class="text-lg font-bold text-sky-900">调整总名额</h3>
              <button @click="editingSlots = null" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div class="p-6 space-y-4">
              <div class="text-sm text-gray-600">
                <p>场次：<span class="font-medium text-sky-900">{{ editingSlots.title }}</span></p>
                <p class="mt-1">当前名额：<span class="font-medium">{{ editingSlots.total_slots }}</span></p>
                <p class="mt-1">已售（含待支付）：<span class="font-medium text-red-500">{{ editingSlots.total_slots - editingSlots.available_slots }}</span></p>
                <p class="mt-2 text-xs text-gray-400">注意：总名额不能小于已售数量</p>
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">新总名额</label>
                <input v-model.number="newSlotCount" type="number" :min="editingSlots.total_slots - editingSlots.available_slots" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-sky-300" />
              </div>
            </div>
            <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
              <button @click="editingSlots = null" class="px-4 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 text-sm">取消</button>
              <button @click="saveSlots" :disabled="processingSession === editingSlots.id"
                class="px-4 py-2 rounded-xl bg-sky-500 text-white hover:bg-sky-600 disabled:bg-gray-300 text-sm font-medium">
                {{ processingSession === editingSlots.id ? '保存中...' : '确认调整' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 场次详情弹窗 -->
        <div v-if="showSessionDetail && sessionDetail" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div class="bg-white rounded-2xl shadow-xl max-w-lg w-full">
            <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
              <h3 class="text-lg font-bold text-sky-900">场次详情</h3>
              <button @click="closeSessionDetail" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div class="p-6 space-y-4">
              <div>
                <h4 class="font-bold text-sky-900">{{ sessionDetail.title }}</h4>
                <p v-if="sessionDetail.description" class="text-sm text-gray-500 mt-1">{{ sessionDetail.description }}</p>
              </div>
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div class="text-gray-400 text-xs">教练</div>
                  <div class="font-medium">{{ sessionDetail.coach }}</div>
                </div>
                <div>
                  <div class="text-gray-400 text-xs">状态</div>
                  <span :class="sessionStatusClass(sessionDetail.status)" class="px-2 py-0.5 rounded-full text-xs font-medium">
                    {{ sessionStatusLabel(sessionDetail.status) }}
                  </span>
                </div>
                <div>
                  <div class="text-gray-400 text-xs">开始时间</div>
                  <div class="font-medium">{{ new Date(sessionDetail.start_time).toLocaleString('zh-CN') }}</div>
                </div>
                <div>
                  <div class="text-gray-400 text-xs">结束时间</div>
                  <div class="font-medium">{{ new Date(sessionDetail.end_time).toLocaleString('zh-CN') }}</div>
                </div>
                <div>
                  <div class="text-gray-400 text-xs">总名额</div>
                  <div class="font-medium">{{ sessionDetail.total_slots }}</div>
                </div>
                <div>
                  <div class="text-gray-400 text-xs">剩余名额</div>
                  <div class="font-medium" :class="sessionDetail.available_slots <= 3 ? 'text-red-500' : 'text-green-600'">{{ sessionDetail.available_slots }}</div>
                </div>
              </div>
              <div class="pt-4 border-t border-gray-100">
                <h5 class="font-bold text-gray-700 mb-3">报名统计</h5>
                <div class="grid grid-cols-3 gap-4 text-center">
                  <div class="bg-sky-50 rounded-xl p-3">
                    <div class="text-2xl font-bold text-sky-600">{{ sessionDetail.booked_count }}</div>
                    <div class="text-xs text-gray-500 mt-1">已报人数</div>
                  </div>
                  <div class="bg-yellow-50 rounded-xl p-3">
                    <div class="text-2xl font-bold text-yellow-600">{{ sessionDetail.pending_count }}</div>
                    <div class="text-xs text-gray-500 mt-1">待支付占用</div>
                  </div>
                  <div class="bg-green-50 rounded-xl p-3">
                    <div class="text-2xl font-bold text-green-600">¥{{ (sessionDetail.paid_amount / 100).toFixed(0) }}</div>
                    <div class="text-xs text-gray-500 mt-1">实收金额</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="px-6 py-4 border-t border-gray-100 flex justify-end">
              <button @click="closeSessionDetail" class="px-4 py-2 rounded-xl bg-sky-500 text-white hover:bg-sky-600 text-sm font-medium">关闭</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 退款 -->
      <div v-show="activeTab === 'refunds'" class="space-y-4">
        <div class="flex gap-3 items-center">
          <select v-model="refundFilter" @change="loadRefunds" class="border border-gray-200 rounded-xl px-3 py-2 text-sm">
            <option value="">全部状态</option>
            <option value="requested">待审核</option>
            <option value="refunded">已退款</option>
            <option value="rejected">已驳回</option>
          </select>
          <button @click="loadRefunds" class="px-4 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 transition text-sm">🔄 刷新</button>
        </div>

        <div class="bg-white rounded-2xl shadow-sm border border-sky-100 overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-sky-50 text-sky-800">
              <tr>
                <th class="px-4 py-3 text-left">学员</th>
                <th class="px-4 py-3 text-left">场次</th>
                <th class="px-4 py-3 text-left">退款金额</th>
                <th class="px-4 py-3 text-left">原因</th>
                <th class="px-4 py-3 text-left">状态</th>
                <th class="px-4 py-3 text-left">申请时间</th>
                <th class="px-4 py-3 text-left">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in refunds" :key="r.id" class="border-t border-gray-50 hover:bg-gray-50">
                <td class="px-4 py-3">{{ r.student_name }}</td>
                <td class="px-4 py-3">{{ r.session_title }}</td>
                <td class="px-4 py-3 font-medium text-orange-500">¥{{ (r.amount / 100).toFixed(2) }}</td>
                <td class="px-4 py-3 text-gray-600 max-w-xs truncate">{{ r.reason }}</td>
                <td class="px-4 py-3">
                  <span :class="refundStatusClass(r.status)" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ refundStatusLabel(r.status) }}</span>
                </td>
                <td class="px-4 py-3 text-gray-400 text-xs">{{ new Date(r.requested_at).toLocaleString('zh-CN') }}</td>
                <td class="px-4 py-3">
                  <div v-if="r.status === 'requested'" class="flex gap-2">
                    <button @click="approveRefund(r)" :disabled="processingRefund === r.id"
                      class="px-3 py-1 rounded-lg bg-green-500 text-white hover:bg-green-600 disabled:opacity-50 text-xs font-medium">通过</button>
                    <button @click="rejectRefund(r)" :disabled="processingRefund === r.id"
                      class="px-3 py-1 rounded-lg bg-gray-200 text-gray-600 hover:bg-gray-300 disabled:opacity-50 text-xs font-medium">驳回</button>
                  </div>
                  <span v-else class="text-gray-300 text-xs">已处理</span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="refunds.length === 0" class="text-center py-8 text-gray-400">暂无退款申请</div>
        </div>
      </div>

      <!-- 签到管理 -->
      <div v-show="activeTab === 'checkin'" class="space-y-6">
        <div class="bg-white rounded-2xl shadow-sm border border-sky-100 p-6">
          <h3 class="text-lg font-bold text-sky-900 mb-4">📋 现场签到</h3>
          <div class="space-y-4">
            <div class="flex gap-3">
              <input
                v-model="checkinCode"
                type="text"
                placeholder="请输入 8 位核销码，或点击扫码模拟"
                maxlength="8"
                class="flex-1 border border-gray-200 rounded-xl px-4 py-3 font-mono text-lg tracking-wider outline-none focus:ring-2 focus:ring-sky-300"
                @keyup.enter="doCheckin"
              />
              <button
                @click="simulateScan"
                class="px-6 py-3 rounded-xl bg-emerald-500 text-white hover:bg-emerald-600 transition font-medium"
              >
                📱 扫码模拟
              </button>
              <button
                @click="doCheckin"
                :disabled="checkingIn || !checkinCode.trim()"
                class="px-6 py-3 rounded-xl bg-sky-500 text-white hover:bg-sky-600 transition font-medium disabled:bg-gray-300"
              >
                {{ checkingIn ? '签到中...' : '确认签到' }}
              </button>
            </div>

            <div v-if="checkinResult" class="mt-6">
              <div
                :class="checkinResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'"
                class="border rounded-xl p-5"
              >
                <div class="flex items-start gap-3">
                  <div class="text-3xl">
                    {{ checkinResult.success ? '✅' : '❌' }}
                  </div>
                  <div class="flex-1">
                    <div
                      :class="checkinResult.success ? 'text-green-800' : 'text-red-800'"
                      class="font-bold text-lg mb-2"
                    >
                      {{ checkinResult.message }}
                    </div>

                    <div v-if="checkinResult.success && checkinResult.student_name" class="mt-4 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div class="text-gray-500">学员姓名</div>
                        <div class="font-bold text-gray-900">{{ checkinResult.student_name }}</div>
                      </div>
                      <div>
                        <div class="text-gray-500">学员年龄</div>
                        <div class="font-bold text-gray-900">{{ checkinResult.student_age }} 岁</div>
                      </div>
                      <div>
                        <div class="text-gray-500">家长姓名</div>
                        <div class="font-bold text-gray-900">{{ checkinResult.parent_name }}</div>
                      </div>
                      <div>
                        <div class="text-gray-500">家长电话</div>
                        <div class="font-bold text-gray-900">{{ checkinResult.parent_phone }}</div>
                      </div>
                      <div class="col-span-2">
                        <div class="text-gray-500">场次</div>
                        <div class="font-bold text-gray-900">{{ checkinResult.session_title }}</div>
                      </div>
                      <div>
                        <div class="text-gray-500">教练</div>
                        <div class="font-bold text-gray-900">{{ checkinResult.coach }}</div>
                      </div>
                      <div>
                        <div class="text-gray-500">签到时间</div>
                        <div class="font-bold text-gray-900">
                          {{ checkinResult.checked_in_at ? new Date(checkinResult.checked_in_at).toLocaleString('zh-CN') : '-' }}
                        </div>
                      </div>
                    </div>

                    <div v-if="!checkinResult.success && checkinResult.order_id" class="mt-4 text-sm text-gray-600">
                      <p>学员：{{ checkinResult.student_name }}</p>
                      <p v-if="checkinResult.checked_in_at">上次签到：{{ new Date(checkinResult.checked_in_at).toLocaleString('zh-CN') }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 签到名册弹窗 -->
      <div v-if="showCheckinRoster" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-2xl shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
            <h3 class="text-lg font-bold text-sky-900">📋 场次签到名册</h3>
            <button @click="closeCheckinRoster" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
          </div>

          <div v-if="loadingRoster" class="p-12 text-center text-sky-500">加载中...</div>

          <div v-else-if="checkinRoster" class="p-6">
            <div class="mb-6">
              <h4 class="font-bold text-sky-900 text-lg">{{ checkinRoster.session_title }}</h4>
              <div class="text-sm text-gray-500 mt-1">
                教练：{{ checkinRoster.coach }} · {{ new Date(checkinRoster.start_time).toLocaleString('zh-CN') }} — {{ new Date(checkinRoster.end_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
              </div>
            </div>

            <div class="grid grid-cols-3 gap-4 mb-6">
              <div class="bg-sky-50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-sky-600">{{ checkinRoster.total_booked }}</div>
                <div class="text-xs text-gray-500 mt-1">已报名</div>
              </div>
              <div class="bg-green-50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-green-600">{{ checkinRoster.total_checked_in }}</div>
                <div class="text-xs text-gray-500 mt-1">已签到</div>
              </div>
              <div class="bg-red-50 rounded-xl p-4 text-center">
                <div class="text-3xl font-bold text-red-600">{{ checkinRoster.total_absent }}</div>
                <div class="text-xs text-gray-500 mt-1">未到</div>
              </div>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead class="bg-sky-50 text-sky-800">
                  <tr>
                    <th class="px-4 py-3 text-left">学员</th>
                    <th class="px-4 py-3 text-left">家长</th>
                    <th class="px-4 py-3 text-left">电话</th>
                    <th class="px-4 py-3 text-left">实付</th>
                    <th class="px-4 py-3 text-left">支付时间</th>
                    <th class="px-4 py-3 text-left">签到状态</th>
                    <th class="px-4 py-3 text-left">签到时间</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="o in checkinRoster.orders" :key="o.id" class="border-t border-gray-50 hover:bg-gray-50">
                    <td class="px-4 py-3">
                      <div class="font-medium">{{ o.student_name }}</div>
                      <div class="text-xs text-gray-400">{{ o.student_age }} 岁</div>
                    </td>
                    <td class="px-4 py-3">{{ o.parent_name }}</td>
                    <td class="px-4 py-3">{{ o.parent_phone }}</td>
                    <td class="px-4 py-3 font-medium">¥{{ (o.amount / 100).toFixed(2) }}</td>
                    <td class="px-4 py-3 text-gray-400 text-xs">
                      {{ o.paid_at ? new Date(o.paid_at).toLocaleString('zh-CN') : '-' }}
                    </td>
                    <td class="px-4 py-3">
                      <span :class="checkinStatusClass(o.checkin_status)" class="px-2 py-0.5 rounded-full text-xs font-medium">
                        {{ checkinStatusLabel(o.checkin_status) }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-gray-400 text-xs">
                      {{ o.checked_in_at ? new Date(o.checked_in_at).toLocaleString('zh-CN') : '-' }}
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="checkinRoster.orders.length === 0" class="text-center py-8 text-gray-400">暂无报名记录</div>
            </div>
          </div>

          <div class="px-6 py-4 border-t border-gray-100 flex justify-end">
            <button @click="closeCheckinRoster" class="px-4 py-2 rounded-xl bg-sky-500 text-white hover:bg-sky-600 text-sm font-medium">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useApi } from '@/composables/useApi'

const { get, post, patch, download } = useApi()
const adminSecret = ref('changeme')
const authenticated = ref(false)
const loginError = ref('')
const filterStatus = ref('')
const exporting = ref(false)
const activeTab = ref<'orders' | 'sessions' | 'coupons' | 'refunds' | 'checkin'>('orders')

const tabs = [
  { key: 'orders' as const, label: '订单' },
  { key: 'sessions' as const, label: '场次管理' },
  { key: 'coupons' as const, label: '优惠券' },
  { key: 'refunds' as const, label: '退款审批' },
  { key: 'checkin' as const, label: '签到管理' },
]

const stats = ref({
  total_orders: 0, paid_orders: 0, pending_orders: 0, expired_orders: 0,
  refunded_orders: 0, refunding_orders: 0, total_revenue: 0, refunded_amount: 0,
  total_discount: 0, pending_refunds: 0,
})

interface OrderRow {
  id: string
  student_name: string
  student_age: number
  parent_name: string
  parent_phone: string
  amount: number
  discount_amount: number
  coupon_code: string | null
  status: string
  created_at: string
}

interface CouponRow {
  id: string
  code: string
  name: string
  discount_type: string
  discount_value: number
  min_amount: number
  max_discount: number
  total_quantity: number
  used_quantity: number
  valid_from: string
  valid_until: string
  status: string
}

interface RefundRow {
  id: string
  order_id: string
  amount: number
  reason: string
  status: string
  requested_at: string
  student_name: string
  session_title: string
}

interface SessionRow {
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

interface SessionDetailRow extends SessionRow {
  booked_count: number
  pending_count: number
  paid_amount: number
}

interface CheckinResult {
  success: boolean
  message: string
  order_id: string | null
  student_name: string | null
  student_age: number | null
  parent_name: string | null
  parent_phone: string | null
  session_title: string | null
  coach: string | null
  start_time: string | null
  end_time: string | null
  checked_in_at: string | null
}

interface CheckinOrderRow {
  id: string
  student_name: string
  student_age: number
  parent_name: string
  parent_phone: string
  checkin_status: string
  checked_in_at: string | null
  paid_at: string | null
  amount: number
}

interface SessionCheckinResult {
  session_id: string
  session_title: string
  coach: string
  start_time: string
  end_time: string
  total_booked: number
  total_checked_in: number
  total_absent: number
  orders: CheckinOrderRow[]
}

const orders = ref<OrderRow[]>([])
const coupons = ref<CouponRow[]>([])
const refunds = ref<RefundRow[]>([])
const sessions = ref<SessionRow[]>([])
const sessionDetail = ref<SessionDetailRow | null>(null)

const showCouponForm = ref(false)
const creatingCoupon = ref(false)
const couponError = ref('')
const refundFilter = ref('')
const processingRefund = ref<string | null>(null)

const showSessionForm = ref(false)
const showSessionDetail = ref(false)
const editingSession = ref<SessionRow | null>(null)
const creatingSession = ref(false)
const sessionError = ref('')
const processingSession = ref<string | null>(null)
const editingSlots = ref<SessionRow | null>(null)
const newSlotCount = ref(0)

const checkinCode = ref('')
const checkingIn = ref(false)
const checkinResult = ref<CheckinResult | null>(null)
const showCheckinRoster = ref(false)
const checkinRoster = ref<SessionCheckinResult | null>(null)
const loadingRoster = ref(false)

const sessionForm = reactive({
  title: '',
  description: '',
  coach: '',
  start_time: '',
  end_time: '',
  total_slots: 10,
  price: 199,
})

const couponForm = reactive({
  code: '',
  name: '',
  discount_type: 'fixed',
  discount_value: 50,
  min_amount: 0,
  max_discount: 0,
  total_quantity: 100,
  valid_from: '',
  valid_until: '',
})

const statCards = computed(() => [
  { label: '总订单', value: stats.value.total_orders, color: 'text-sky-600' },
  { label: '已支付', value: stats.value.paid_orders, color: 'text-green-600' },
  { label: '待支付', value: stats.value.pending_orders, color: 'text-yellow-600' },
  { label: '已退款', value: stats.value.refunded_orders, color: 'text-gray-500' },
  { label: '总收入', value: `¥${(stats.value.total_revenue / 100).toFixed(0)}`, color: 'text-orange-600' },
  { label: '优惠总额', value: `¥${(stats.value.total_discount / 100).toFixed(0)}`, color: 'text-pink-600' },
  { label: '待审退款', value: stats.value.pending_refunds, color: 'text-red-600' },
])

function authHeader() {
  return { 'X-Admin-Secret': adminSecret.value }
}

function orderStatusLabel(s: string) {
  const m: Record<string, string> = { pending: '待支付', paid: '已支付', expired: '已过期', cancelled: '已取消', refunding: '退款审核中', refunded: '已退款' }
  return m[s] || s
}

function orderStatusClass(s: string) {
  const m: Record<string, string> = { pending: 'bg-yellow-100 text-yellow-700', paid: 'bg-green-100 text-green-700', expired: 'bg-red-100 text-red-700', refunding: 'bg-amber-100 text-amber-700', refunded: 'bg-gray-100 text-gray-600' }
  return m[s] || 'bg-gray-100 text-gray-600'
}

function refundStatusLabel(s: string) {
  const m: Record<string, string> = { requested: '待审核', refunded: '已退款', rejected: '已驳回' }
  return m[s] || s
}

function refundStatusClass(s: string) {
  const m: Record<string, string> = { requested: 'bg-amber-100 text-amber-700', refunded: 'bg-green-100 text-green-700', rejected: 'bg-gray-100 text-gray-500' }
  return m[s] || 'bg-gray-100 text-gray-600'
}

function couponDiscountText(c: CouponRow) {
  if (c.discount_type === 'fixed') return `立减 ¥${(c.discount_value / 100).toFixed(0)}`
  const cap = c.max_discount > 0 ? `，最高¥${(c.max_discount / 100).toFixed(0)}` : ''
  return `立减 ${c.discount_value}%${cap}`
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN')
}

async function login() {
  loginError.value = ''
  try {
    await get('/admin/stats', authHeader())
    authenticated.value = true
    loadStats()
    loadOrders()
  } catch (e: any) {
    loginError.value = e.message || '认证失败'
  }
}

function switchTab(key: 'orders' | 'sessions' | 'coupons' | 'refunds' | 'checkin') {
  activeTab.value = key
  if (key === 'sessions' && sessions.value.length === 0) loadSessions()
  if (key === 'coupons' && coupons.value.length === 0) loadCoupons()
  if (key === 'refunds') loadRefunds()
  if (key === 'checkin') {
    checkinCode.value = ''
    checkinResult.value = null
  }
}

async function loadStats() {
  try {
    stats.value = await get('/admin/stats', authHeader())
  } catch {}
}

async function loadOrders() {
  try {
    const path = filterStatus.value ? `/admin/orders?status=${filterStatus.value}` : '/admin/orders'
    orders.value = await get<OrderRow[]>(path, authHeader())
  } catch {}
}

async function loadCoupons() {
  try {
    coupons.value = await get<CouponRow[]>('/admin/coupons', authHeader())
  } catch {}
}

async function loadRefunds() {
  try {
    const path = refundFilter.value ? `/admin/refunds?status=${refundFilter.value}` : '/admin/refunds'
    refunds.value = await get<RefundRow[]>(path, authHeader())
    loadStats()
  } catch {}
}

async function createCoupon() {
  couponError.value = ''
  if (!couponForm.code || !couponForm.name) { couponError.value = '请填写优惠码与名称'; return }
  if (!couponForm.valid_from || !couponForm.valid_until) { couponError.value = '请选择有效期'; return }
  creatingCoupon.value = true
  try {
    const isPercent = couponForm.discount_type === 'percent'
    await post('/admin/coupons', {
      code: couponForm.code.trim().toUpperCase(),
      name: couponForm.name.trim(),
      discount_type: couponForm.discount_type,
      discount_value: isPercent ? couponForm.discount_value : Math.round(couponForm.discount_value * 100),
      min_amount: Math.round((couponForm.min_amount || 0) * 100),
      max_discount: isPercent ? Math.round((couponForm.max_discount || 0) * 100) : 0,
      total_quantity: couponForm.total_quantity,
      valid_from: new Date(couponForm.valid_from).toISOString(),
      valid_until: new Date(couponForm.valid_until).toISOString(),
    }, authHeader())
    showCouponForm.value = false
    couponForm.code = ''
    couponForm.name = ''
    await loadCoupons()
  } catch (e: any) {
    couponError.value = e.message || '创建失败'
  } finally {
    creatingCoupon.value = false
  }
}

async function toggleCoupon(c: CouponRow) {
  const next = c.status === 'active' ? 'disabled' : 'active'
  try {
    await patch(`/admin/coupons/${c.id}`, { status: next }, authHeader())
    c.status = next
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

async function approveRefund(r: RefundRow) {
  processingRefund.value = r.id
  try {
    await post(`/admin/refunds/${r.id}/approve`, { operator: '管理员' }, authHeader())
    await loadRefunds()
  } catch (e: any) {
    alert(e.message || '审批失败')
  } finally {
    processingRefund.value = null
  }
}

async function rejectRefund(r: RefundRow) {
  const remark = prompt('请输入驳回原因（可选）') ?? undefined
  processingRefund.value = r.id
  try {
    await post(`/admin/refunds/${r.id}/reject`, { remark }, authHeader())
    await loadRefunds()
  } catch (e: any) {
    alert(e.message || '驳回失败')
  } finally {
    processingRefund.value = null
  }
}

function sessionStatusLabel(s: string) {
  const m: Record<string, string> = { open: '可报名', closed: '已关闭', full: '已满' }
  return m[s] || s
}

function sessionStatusClass(s: string) {
  const m: Record<string, string> = {
    open: 'bg-green-100 text-green-700',
    closed: 'bg-gray-100 text-gray-500',
    full: 'bg-red-100 text-red-700'
  }
  return m[s] || 'bg-gray-100 text-gray-600'
}

async function loadSessions() {
  try {
    sessions.value = await get<SessionRow[]>('/admin/sessions', authHeader())
  } catch {}
}

function openCreateSession() {
  editingSession.value = null
  sessionForm.title = ''
  sessionForm.description = ''
  sessionForm.coach = ''
  sessionForm.start_time = ''
  sessionForm.end_time = ''
  sessionForm.total_slots = 10
  sessionForm.price = 199
  showSessionForm.value = true
  sessionError.value = ''
}

function formatForDatetimeLocal(iso: string): string {
  return iso.slice(0, 16)
}

function openEditSession(s: SessionRow) {
  editingSession.value = s
  sessionForm.title = s.title
  sessionForm.description = s.description || ''
  sessionForm.coach = s.coach
  sessionForm.start_time = formatForDatetimeLocal(s.start_time)
  sessionForm.end_time = formatForDatetimeLocal(s.end_time)
  sessionForm.total_slots = s.total_slots
  sessionForm.price = s.price / 100
  showSessionForm.value = true
  sessionError.value = ''
}

function toLocalISOString(datetimeLocal: string): string {
  if (!datetimeLocal) return ''
  const [datePart, timePart] = datetimeLocal.split('T')
  return `${datePart}T${timePart}:00`
}

async function saveSession() {
  sessionError.value = ''
  if (!sessionForm.title || !sessionForm.coach) { sessionError.value = '请填写标题与教练'; return }
  if (!sessionForm.start_time || !sessionForm.end_time) { sessionError.value = '请选择时间'; return }
  if (new Date(sessionForm.end_time) <= new Date(sessionForm.start_time)) { sessionError.value = '结束时间必须晚于开始时间'; return }

  creatingSession.value = true
  try {
    const desc = sessionForm.description.trim()
    const payload = {
      title: sessionForm.title.trim(),
      description: desc || null,
      coach: sessionForm.coach.trim(),
      start_time: toLocalISOString(sessionForm.start_time),
      end_time: toLocalISOString(sessionForm.end_time),
      total_slots: sessionForm.total_slots,
      price: Math.round(sessionForm.price * 100),
    }
    if (editingSession.value) {
      const { total_slots, ...updatePayload } = payload
      await patch(`/admin/sessions/${editingSession.value.id}`, updatePayload, authHeader())
    } else {
      await post('/admin/sessions', payload, authHeader())
    }
    showSessionForm.value = false
    await loadSessions()
  } catch (e: any) {
    sessionError.value = e.message || '保存失败'
  } finally {
    creatingSession.value = false
  }
}

async function toggleSessionStatus(s: SessionRow) {
  const next = s.status === 'open' ? 'closed' : 'open'
  processingSession.value = s.id
  try {
    await patch(`/admin/sessions/${s.id}/status`, { status: next }, authHeader())
    s.status = next
  } catch (e: any) {
    alert(e.message || '操作失败')
  } finally {
    processingSession.value = null
  }
}

function openSlotsEditor(s: SessionRow) {
  editingSlots.value = s
  newSlotCount.value = s.total_slots
}

async function saveSlots() {
  if (!editingSlots.value) return
  processingSession.value = editingSlots.value.id
  try {
    const updated = await patch<SessionRow>(
      `/admin/sessions/${editingSlots.value.id}/slots`,
      { total_slots: newSlotCount.value },
      authHeader()
    )
    const idx = sessions.value.findIndex(s => s.id === updated.id)
    if (idx !== -1) sessions.value[idx] = updated
    editingSlots.value = null
  } catch (e: any) {
    alert(e.message || '调整失败')
  } finally {
    processingSession.value = null
  }
}

async function openSessionDetail(s: SessionRow) {
  try {
    sessionDetail.value = await get<SessionDetailRow>(`/admin/sessions/${s.id}/detail`, authHeader())
    showSessionDetail.value = true
  } catch (e: any) {
    alert(e.message || '获取详情失败')
  }
}

function closeSessionDetail() {
  showSessionDetail.value = false
  sessionDetail.value = null
}

async function doCheckin() {
  if (!checkinCode.value.trim()) return
  checkingIn.value = true
  checkinResult.value = null
  try {
    checkinResult.value = await post<CheckinResult>(
      '/admin/checkin',
      { checkin_code: checkinCode.value.trim().toUpperCase() },
      authHeader()
    )
  } catch (e: any) {
    checkinResult.value = {
      success: false,
      message: e.message || '签到失败',
      order_id: null,
      student_name: null,
      student_age: null,
      parent_name: null,
      parent_phone: null,
      session_title: null,
      coach: null,
      start_time: null,
      end_time: null,
      checked_in_at: null,
    }
  } finally {
    checkingIn.value = false
  }
}

function simulateScan() {
  const mockCodes = ['ABC12345', 'DEF67890', 'GHI11111']
  const randomCode = mockCodes[Math.floor(Math.random() * mockCodes.length)]
  checkinCode.value = randomCode
  doCheckin()
}

function checkinStatusLabel(s: string) {
  const m: Record<string, string> = { pending: '未签到', checked_in: '已签到' }
  return m[s] || s
}

function checkinStatusClass(s: string) {
  const m: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    checked_in: 'bg-green-100 text-green-700'
  }
  return m[s] || 'bg-gray-100 text-gray-600'
}

async function openCheckinRoster(s: SessionRow) {
  loadingRoster.value = true
  showCheckinRoster.value = true
  checkinRoster.value = null
  try {
    checkinRoster.value = await get<SessionCheckinResult>(
      `/admin/sessions/${s.id}/checkin`,
      authHeader()
    )
  } catch (e: any) {
    alert(e.message || '获取签到名册失败')
    showCheckinRoster.value = false
  } finally {
    loadingRoster.value = false
  }
}

function closeCheckinRoster() {
  showCheckinRoster.value = false
  checkinRoster.value = null
}

async function exportCsv() {
  exporting.value = true
  try {
    await download('/admin/orders/export', 'orders.csv', authHeader())
  } catch (e: any) {
    alert(e.message || '导出失败')
  } finally {
    exporting.value = false
  }
}
</script>
