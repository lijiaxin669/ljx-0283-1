function genId(): string {
  return crypto.randomUUID()
}

function generateCheckinCode(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let result = ''
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

interface MockSession {
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

interface MockOrder {
  id: string
  session_id: string
  student_name: string
  student_age: number
  parent_name: string
  parent_phone: string
  status: string
  amount: number
  original_amount: number
  discount_amount: number
  coupon_id: string | null
  coupon_code: string | null
  expire_at: string
  checkin_code: string | null
  checkin_status: string
  checked_in_at: string | null
  created_at: string
}

interface MockPayment {
  id: string
  order_id: string
  payment_id: string
  channel: string
  amount: number
  status: string
  paid_at: string | null
  created_at: string
}

interface MockCoupon {
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
  created_at: string
}

interface MockRefund {
  id: string
  order_id: string
  payment_id: string
  amount: number
  reason: string
  status: string
  operator: string | null
  remark: string | null
  requested_at: string
  processed_at: string | null
  student_name: string
  session_title: string
}

const ADMIN_SECRET = 'changeme'

const sessions: MockSession[] = [
  {
    id: 'a0000000-0000-0000-0000-000000000001',
    title: '亲子启蒙班 A',
    description: '适合 1–3 岁宝宝，家长陪同入水',
    coach: '王教练',
    start_time: '2026-07-01T09:00:00',
    end_time: '2026-07-01T10:00:00',
    total_slots: 10,
    available_slots: 10,
    price: 19900,
    status: 'open',
  },
  {
    id: 'a0000000-0000-0000-0000-000000000002',
    title: '亲子启蒙班 B',
    description: '适合 1–3 岁宝宝，家长陪同入水',
    coach: '李教练',
    start_time: '2026-07-01T10:30:00',
    end_time: '2026-07-01T11:30:00',
    total_slots: 10,
    available_slots: 10,
    price: 19900,
    status: 'open',
  },
  {
    id: 'a0000000-0000-0000-0000-000000000003',
    title: '幼儿基础班',
    description: '适合 3–6 岁儿童，学习基础泳姿',
    coach: '张教练',
    start_time: '2026-07-02T09:00:00',
    end_time: '2026-07-02T10:30:00',
    total_slots: 8,
    available_slots: 3,
    price: 25900,
    status: 'open',
  },
  {
    id: 'a0000000-0000-0000-0000-000000000004',
    title: '少儿进阶班',
    description: '适合 6–12 岁少儿，提升游泳技巧',
    coach: '赵教练',
    start_time: '2026-07-03T14:00:00',
    end_time: '2026-07-03T16:00:00',
    total_slots: 12,
    available_slots: 12,
    price: 29900,
    status: 'open',
  },
]

const coupons: MockCoupon[] = [
  {
    id: 'c0000000-0000-0000-0000-000000000001',
    code: 'SWIM50',
    name: '新生立减 50 元',
    discount_type: 'fixed',
    discount_value: 5000,
    min_amount: 0,
    max_discount: 0,
    total_quantity: 100,
    used_quantity: 0,
    valid_from: '2026-06-01T00:00:00',
    valid_until: '2026-12-31T23:59:59',
    status: 'active',
    created_at: '2026-06-01T00:00:00',
  },
  {
    id: 'c0000000-0000-0000-0000-000000000002',
    code: 'SUMMER20',
    name: '暑期 8 折券',
    discount_type: 'percent',
    discount_value: 20,
    min_amount: 20000,
    max_discount: 8000,
    total_quantity: 50,
    used_quantity: 0,
    valid_from: '2026-06-01T00:00:00',
    valid_until: '2026-09-30T23:59:59',
    status: 'active',
    created_at: '2026-06-01T00:00:00',
  },
  {
    id: 'c0000000-0000-0000-0000-000000000003',
    code: 'FULL100',
    name: '满 200 减 100',
    discount_type: 'fixed',
    discount_value: 10000,
    min_amount: 20000,
    max_discount: 0,
    total_quantity: 30,
    used_quantity: 0,
    valid_from: '2026-06-01T00:00:00',
    valid_until: '2026-12-31T23:59:59',
    status: 'active',
    created_at: '2026-06-01T00:00:00',
  },
]

const orders: MockOrder[] = []
const payments: MockPayment[] = []
const refunds: MockRefund[] = []

function computeDiscount(coupon: MockCoupon, amount: number): number {
  if (amount < coupon.min_amount) return 0
  let discount = 0
  if (coupon.discount_type === 'fixed') {
    discount = Math.min(coupon.discount_value, amount)
  } else if (coupon.discount_type === 'percent') {
    discount = Math.floor((amount * coupon.discount_value) / 100)
    if (coupon.max_discount > 0) discount = Math.min(discount, coupon.max_discount)
  }
  return Math.max(0, Math.min(discount, amount))
}

function checkUsable(coupon: MockCoupon | undefined, amount: number): { usable: boolean; message: string } {
  const now = Date.now()
  if (!coupon) return { usable: false, message: '优惠券不存在' }
  if (coupon.status !== 'active') return { usable: false, message: '优惠券已停用' }
  if (now < new Date(coupon.valid_from).getTime()) return { usable: false, message: '优惠券尚未生效' }
  if (now > new Date(coupon.valid_until).getTime()) return { usable: false, message: '优惠券已过期' }
  if (coupon.used_quantity >= coupon.total_quantity) return { usable: false, message: '优惠券已被领完' }
  if (amount < coupon.min_amount) {
    return { usable: false, message: `订单金额需满 ¥${(coupon.min_amount / 100).toFixed(2)} 方可使用` }
  }
  if (computeDiscount(coupon, amount) <= 0) return { usable: false, message: '该优惠券对此订单无优惠' }
  return { usable: true, message: '可用' }
}

function releaseCoupon(couponId: string | null) {
  if (!couponId) return
  const coupon = coupons.find(c => c.id === couponId)
  if (coupon && coupon.used_quantity > 0) coupon.used_quantity--
}

function checkExpiry() {
  const now = Date.now()
  for (const order of orders) {
    if (order.status === 'pending' && new Date(order.expire_at).getTime() < now) {
      order.status = 'expired'
      const session = sessions.find(s => s.id === order.session_id)
      if (session) {
        session.available_slots++
        if (session.status === 'full') session.status = 'open'
      }
      releaseCoupon(order.coupon_id)
    }
  }
}

function verifyAdmin(headers?: Record<string, string>) {
  if (!headers || headers['X-Admin-Secret'] !== ADMIN_SECRET) {
    throw new Error('管理端认证失败')
  }
}

export const mockApi = {
  async get(path: string, headers?: Record<string, string>): Promise<any> {
    await delay(80)
    checkExpiry()

    const sessionsListMatch = path.match(/^\/sessions(\?.*)?$/)
    if (sessionsListMatch) {
      const urlObj = new URL(path, 'http://localhost')
      const dateFilter = urlObj.searchParams.get('date_filter')
      const coachFilter = urlObj.searchParams.get('coach')
      const statusFilter = urlObj.searchParams.get('status')
      const sortBy = urlObj.searchParams.get('sort_by')
      const sortOrder = urlObj.searchParams.get('sort_order') || 'asc'

      let result = sessions.map(s => ({ ...s }))

      if (dateFilter) {
        result = result.filter(s => s.start_time.startsWith(dateFilter))
      }
      if (coachFilter) {
        result = result.filter(s => s.coach === coachFilter)
      }
      if (statusFilter) {
        result = result.filter(s => s.status === statusFilter)
      }

      result.sort((a, b) => {
        let aVal: string | number = a.start_time
        let bVal: string | number = b.start_time
        if (sortBy === 'price') {
          aVal = a.price
          bVal = b.price
        } else if (sortBy === 'available_slots') {
          aVal = a.available_slots
          bVal = b.available_slots
        }
        if (typeof aVal === 'string' && typeof bVal === 'string') {
          return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
        }
        return sortOrder === 'asc' ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number)
      })

      return result
    }

    if (path === '/sessions/coaches') {
      return [...new Set(sessions.map(s => s.coach))].sort()
    }

    const sessionMatch = path.match(/^\/sessions\/([a-f0-9-]+)$/)
    if (sessionMatch) {
      const s = sessions.find(s => s.id === sessionMatch[1])
      if (!s) throw new Error('场次不存在')
      return { ...s }
    }

    if (path === '/admin/stats') {
      verifyAdmin(headers)
      return {
        total_orders: orders.length,
        paid_orders: orders.filter(o => o.status === 'paid').length,
        pending_orders: orders.filter(o => o.status === 'pending').length,
        expired_orders: orders.filter(o => o.status === 'expired').length,
        refunded_orders: orders.filter(o => o.status === 'refunded').length,
        refunding_orders: orders.filter(o => o.status === 'refunding').length,
        total_revenue: orders.filter(o => o.status === 'paid').reduce((sum, o) => sum + o.amount, 0),
        refunded_amount: orders.filter(o => o.status === 'refunded').reduce((sum, o) => sum + o.amount, 0),
        total_discount: orders.filter(o => o.status === 'paid' || o.status === 'refunded').reduce((sum, o) => sum + o.discount_amount, 0),
        pending_refunds: refunds.filter(r => r.status === 'requested').length,
      }
    }

    if (path === '/admin/coupons') {
      verifyAdmin(headers)
      return coupons.map(c => ({ ...c })).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    }

    if (path.startsWith('/admin/refunds')) {
      verifyAdmin(headers)
      const urlObj = new URL(path, 'http://localhost')
      const status = urlObj.searchParams.get('status')
      let result = refunds.map(r => ({ ...r }))
      if (status) result = result.filter(r => r.status === status)
      return result.sort((a, b) => new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime())
    }

    if (path.startsWith('/admin/orders')) {
      verifyAdmin(headers)
      const urlObj = new URL(path, 'http://localhost')
      const status = urlObj.searchParams.get('status')
      let result = orders.map(o => ({ ...o }))
      if (status) result = result.filter(o => o.status === status)
      return result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    }

    if (path === '/admin/sessions') {
      verifyAdmin(headers)
      return sessions.map(s => ({ ...s })).sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    }

    const adminSessionDetailMatch = path.match(/^\/admin\/sessions\/([a-f0-9-]+)\/detail$/)
    if (adminSessionDetailMatch) {
      verifyAdmin(headers)
      const s = sessions.find(s => s.id === adminSessionDetailMatch[1])
      if (!s) throw new Error('场次不存在')
      const bookedCount = orders.filter(o => o.session_id === s.id && ['pending', 'paid', 'refunding'].includes(o.status)).length
      const pendingCount = orders.filter(o => o.session_id === s.id && o.status === 'pending').length
      const paidAmount = orders.filter(o => o.session_id === s.id && o.status === 'paid').reduce((sum, o) => sum + o.amount, 0)
      return {
        ...s,
        booked_count: bookedCount,
        pending_count: pendingCount,
        paid_amount: paidAmount,
      }
    }

    const adminSessionCheckinMatch = path.match(/^\/admin\/sessions\/([a-f0-9-]+)\/checkin$/)
    if (adminSessionCheckinMatch) {
      verifyAdmin(headers)
      const s = sessions.find(s => s.id === adminSessionCheckinMatch[1])
      if (!s) throw new Error('场次不存在')
      const sessionOrders = orders.filter(o =>
        o.session_id === s.id && ['paid', 'refunding'].includes(o.status)
      )
      const totalBooked = sessionOrders.length
      const totalCheckedIn = sessionOrders.filter(o => o.checkin_status === 'checked_in').length
      const totalAbsent = totalBooked - totalCheckedIn
      const orderList = sessionOrders.map(o => {
        const payment = payments.find(p => p.order_id === o.id)
        return {
          id: o.id,
          student_name: o.student_name,
          student_age: o.student_age,
          parent_name: o.parent_name,
          parent_phone: o.parent_phone,
          checkin_status: o.checkin_status,
          checked_in_at: o.checked_in_at,
          paid_at: payment?.paid_at || null,
          amount: o.amount,
        }
      })
      return {
        session_id: s.id,
        session_title: s.title,
        coach: s.coach,
        start_time: s.start_time,
        end_time: s.end_time,
        total_booked: totalBooked,
        total_checked_in: totalCheckedIn,
        total_absent: totalAbsent,
        orders: orderList,
      }
    }

    const voucherMatch = path.match(/^\/orders\/([a-f0-9-]+)\/voucher$/)
    if (voucherMatch) {
      const orderId = voucherMatch[1]
      const order = orders.find(o => o.id === orderId && o.status === 'paid')
      if (!order) throw new Error('凭证不存在或订单未支付')
      const session = sessions.find(s => s.id === order.session_id)!
      const payment = payments.find(p => p.order_id === orderId)!
      return {
        order_id: order.id,
        student_name: order.student_name,
        student_age: order.student_age,
        parent_name: order.parent_name,
        parent_phone: order.parent_phone,
        session_title: session.title,
        coach: session.coach,
        start_time: session.start_time,
        end_time: session.end_time,
        amount: order.amount,
        original_amount: order.original_amount,
        discount_amount: order.discount_amount,
        coupon_code: order.coupon_code,
        payment_id: payment.payment_id,
        paid_at: payment.paid_at,
        checkin_code: order.checkin_code || '',
        checkin_status: order.checkin_status,
        checked_in_at: order.checked_in_at,
      }
    }

    const orderMatch = path.match(/^\/orders\/([a-f0-9-]+)$/)
    if (orderMatch) {
      const o = orders.find(o => o.id === orderMatch[1])
      if (!o) throw new Error('订单不存在')
      return { ...o }
    }

    const paymentMatch = path.match(/^\/payments\/(.+)$/)
    if (paymentMatch) {
      const p = payments.find(p => p.payment_id === paymentMatch[1])
      if (!p) throw new Error('支付记录不存在')
      return { ...p }
    }

    throw new Error(`Not found: GET ${path}`)
  },

  async post(path: string, body?: any, headers?: Record<string, string>): Promise<any> {
    await delay(120)
    checkExpiry()

    if (path === '/sessions') {
      const s: MockSession = {
        id: genId(),
        title: body.title,
        description: body.description || null,
        coach: body.coach,
        start_time: body.start_time,
        end_time: body.end_time,
        total_slots: body.total_slots,
        available_slots: body.total_slots,
        price: body.price,
        status: 'open',
      }
      sessions.push(s)
      return { ...s }
    }

    if (path === '/orders') {
      const session = sessions.find(s => s.id === body.session_id)
      if (!session) throw new Error('场次不存在')
      if (session.available_slots <= 0 || session.status !== 'open') {
        throw new Error('库存不足或场次已关闭')
      }

      const originalAmount = session.price
      let discountAmount = 0
      let couponId: string | null = null
      let appliedCode: string | null = null

      if (body.coupon_code) {
        const coupon = coupons.find(c => c.code === body.coupon_code)
        const { usable, message } = checkUsable(coupon, originalAmount)
        if (!usable || !coupon) throw new Error(message)
        discountAmount = computeDiscount(coupon, originalAmount)
        coupon.used_quantity++
        couponId = coupon.id
        appliedCode = coupon.code
      }

      session.available_slots--
      if (session.available_slots === 0) session.status = 'full'
      const expireAt = new Date(Date.now() + 15 * 60 * 1000)
      const order: MockOrder = {
        id: genId(),
        session_id: body.session_id,
        student_name: body.student_name,
        student_age: body.student_age,
        parent_name: body.parent_name,
        parent_phone: body.parent_phone,
        status: 'pending',
        amount: originalAmount - discountAmount,
        original_amount: originalAmount,
        discount_amount: discountAmount,
        coupon_id: couponId,
        coupon_code: appliedCode,
        expire_at: expireAt.toISOString(),
        checkin_code: null,
        checkin_status: 'pending',
        checked_in_at: null,
        created_at: new Date().toISOString(),
      }
      orders.push(order)
      return { ...order }
    }

    if (path === '/coupons/validate') {
      const session = sessions.find(s => s.id === body.session_id)
      if (!session) {
        return { valid: false, code: body.code, original_amount: 0, discount_amount: 0, final_amount: 0, message: '场次不存在' }
      }
      const originalAmount = session.price
      const coupon = coupons.find(c => c.code === body.code)
      const { usable, message } = checkUsable(coupon, originalAmount)
      if (!usable || !coupon) {
        return { valid: false, code: body.code, original_amount: originalAmount, discount_amount: 0, final_amount: originalAmount, message }
      }
      const discount = computeDiscount(coupon, originalAmount)
      return {
        valid: true,
        code: coupon.code,
        name: coupon.name,
        original_amount: originalAmount,
        discount_amount: discount,
        final_amount: originalAmount - discount,
        message: `已抵扣 ¥${(discount / 100).toFixed(2)}`,
      }
    }

    const refundMatch = path.match(/^\/orders\/([a-f0-9-]+)\/refund$/)
    if (refundMatch) {
      const order = orders.find(o => o.id === refundMatch[1])
      if (!order) throw new Error('订单不存在')
      if (order.status === 'refunding') throw new Error('已存在待处理的退款申请')
      if (order.status === 'refunded') throw new Error('订单已退款')
      if (order.status !== 'paid') throw new Error('仅已支付订单可申请退款')
      const payment = payments.find(p => p.order_id === order.id)
      if (!payment) throw new Error('支付记录不存在')
      const session = sessions.find(s => s.id === order.session_id)
      const refund: MockRefund = {
        id: genId(),
        order_id: order.id,
        payment_id: payment.payment_id,
        amount: order.amount,
        reason: body.reason,
        status: 'requested',
        operator: null,
        remark: null,
        requested_at: new Date().toISOString(),
        processed_at: null,
        student_name: order.student_name,
        session_title: session?.title || '',
      }
      order.status = 'refunding'
      refunds.push(refund)
      return { ...refund }
    }

    if (path === '/admin/sessions') {
      verifyAdmin(headers)
      const s: MockSession = {
        id: genId(),
        title: body.title,
        description: body.description || null,
        coach: body.coach,
        start_time: body.start_time,
        end_time: body.end_time,
        total_slots: body.total_slots,
        available_slots: body.total_slots,
        price: body.price,
        status: 'open',
      }
      sessions.push(s)
      return { ...s }
    }

    if (path === '/admin/coupons') {
      verifyAdmin(headers)
      if (coupons.some(c => c.code === body.code)) throw new Error('优惠码已存在')
      if (new Date(body.valid_until).getTime() <= new Date(body.valid_from).getTime()) {
        throw new Error('失效时间必须晚于生效时间')
      }
      const coupon: MockCoupon = {
        id: genId(),
        code: body.code,
        name: body.name,
        discount_type: body.discount_type,
        discount_value: body.discount_value,
        min_amount: body.min_amount || 0,
        max_discount: body.max_discount || 0,
        total_quantity: body.total_quantity,
        used_quantity: 0,
        valid_from: body.valid_from,
        valid_until: body.valid_until,
        status: 'active',
        created_at: new Date().toISOString(),
      }
      coupons.push(coupon)
      return { ...coupon }
    }

    const approveMatch = path.match(/^\/admin\/refunds\/([a-f0-9-]+)\/approve$/)
    if (approveMatch) {
      verifyAdmin(headers)
      const refund = refunds.find(r => r.id === approveMatch[1])
      if (!refund) throw new Error('退款单不存在')
      if (refund.status === 'refunded') return { ...refund }
      if (refund.status !== 'requested') throw new Error('退款单状态不可审批')
      const order = orders.find(o => o.id === refund.order_id)
      if (order) {
        order.status = 'refunded'
        const session = sessions.find(s => s.id === order.session_id)
        if (session) {
          session.available_slots++
          if (session.status === 'full') session.status = 'open'
        }
        releaseCoupon(order.coupon_id)
      }
      const payment = payments.find(p => p.order_id === refund.order_id)
      if (payment) payment.status = 'refunded'
      refund.status = 'refunded'
      refund.operator = body?.operator || '管理员'
      refund.remark = body?.remark || null
      refund.processed_at = new Date().toISOString()
      return { ...refund }
    }

    const rejectMatch = path.match(/^\/admin\/refunds\/([a-f0-9-]+)\/reject$/)
    if (rejectMatch) {
      verifyAdmin(headers)
      const refund = refunds.find(r => r.id === rejectMatch[1])
      if (!refund) throw new Error('退款单不存在')
      if (refund.status === 'rejected') return { ...refund }
      if (refund.status !== 'requested') throw new Error('退款单状态不可驳回')
      const order = orders.find(o => o.id === refund.order_id)
      if (order && order.status === 'refunding') order.status = 'paid'
      refund.status = 'rejected'
      refund.remark = body?.remark || null
      refund.processed_at = new Date().toISOString()
      return { ...refund }
    }

    if (path === '/payments/create') {
      const order = orders.find(o => o.id === body.order_id)
      if (!order) throw new Error('订单不存在')
      if (order.status !== 'pending') throw new Error('订单状态不可支付')
      if (new Date(order.expire_at).getTime() < Date.now()) {
        order.status = 'expired'
        const session = sessions.find(s => s.id === order.session_id)
        if (session) { session.available_slots++; if (session.status === 'full') session.status = 'open' }
        releaseCoupon(order.coupon_id)
        throw new Error('订单已过期')
      }
      const paymentId = `PAY-${Date.now()}-${genId().slice(0, 8)}`
      const payment: MockPayment = {
        id: genId(),
        order_id: body.order_id,
        payment_id: paymentId,
        channel: body.channel,
        amount: order.amount,
        status: 'pending',
        paid_at: null,
        created_at: new Date().toISOString(),
      }
      payments.push(payment)
      return { ...payment }
    }

    if (path === '/payments/callback') {
      const existing = payments.find(p => p.payment_id === body.payment_id)
      if (existing && existing.status === 'paid') return { ...existing }

      const order = orders.find(o => o.id === body.order_id)
      if (!order) throw new Error('订单不存在')
      if (order.status === 'expired') throw new Error('订单已过期')
      if (order.status !== 'pending') throw new Error('订单状态异常')

      if (new Date(order.expire_at).getTime() < Date.now()) {
        order.status = 'expired'
        const session = sessions.find(s => s.id === order.session_id)
        if (session) { session.available_slots++; if (session.status === 'full') session.status = 'open' }
        releaseCoupon(order.coupon_id)
        throw new Error('订单已过期，名额已释放')
      }

      let checkinCode = generateCheckinCode()
      for (let i = 0; i < 5; i++) {
        if (!orders.some(o => o.checkin_code === checkinCode)) break
        checkinCode = generateCheckinCode()
      }

      const payment = payments.find(p => p.order_id === body.order_id)
      if (payment) {
        payment.status = 'paid'
        payment.paid_at = new Date().toISOString()
      }
      order.status = 'paid'
      order.checkin_code = checkinCode
      order.checkin_status = 'pending'
      return payment ? { ...payment } : {
        id: genId(),
        order_id: body.order_id,
        payment_id: body.payment_id,
        channel: body.channel,
        amount: body.amount,
        status: 'paid',
        paid_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      }
    }

    if (path === '/admin/checkin') {
      verifyAdmin(headers)
      const code = body.checkin_code.toUpperCase()
      const order = orders.find(o => o.checkin_code === code)
      if (!order) {
        return { success: false, message: '核销码无效或不存在' }
      }
      if (order.status !== 'paid') {
        if (order.status === 'refunded' || order.status === 'refunding') {
          return { success: false, message: '该订单已申请退款或已退款' }
        }
        return { success: false, message: `订单状态异常：${order.status}` }
      }
      const session = sessions.find(s => s.id === order.session_id)
      if (!session) {
        return { success: false, message: '关联场次不存在' }
      }
      const sessionDate = session.start_time.split('T')[0]
      const today = new Date().toISOString().split('T')[0]
      if (sessionDate !== today) {
        return {
          success: false,
          message: `场次日期不匹配，该场次为 ${sessionDate} 的课程`
        }
      }
      if (order.checkin_status === 'checked_in') {
        return {
          success: false,
          message: '该订单已签到，请勿重复签到',
          order_id: order.id,
          student_name: order.student_name,
          checked_in_at: order.checked_in_at,
        }
      }
      order.checkin_status = 'checked_in'
      order.checked_in_at = new Date().toISOString()
      const payment = payments.find(p => p.order_id === order.id)
      return {
        success: true,
        message: '签到成功',
        order_id: order.id,
        student_name: order.student_name,
        student_age: order.student_age,
        parent_name: order.parent_name,
        parent_phone: order.parent_phone,
        session_title: session.title,
        coach: session.coach,
        start_time: session.start_time,
        end_time: session.end_time,
        checked_in_at: order.checked_in_at,
      }
    }

    throw new Error(`Not found: POST ${path}`)
  },

  async patch(path: string, body?: any, headers?: Record<string, string>): Promise<any> {
    await delay(100)

    const sessionSlotsMatch = path.match(/^\/admin\/sessions\/([a-f0-9-]+)\/slots$/)
    if (sessionSlotsMatch) {
      verifyAdmin(headers)
      const s = sessions.find(s => s.id === sessionSlotsMatch[1])
      if (!s) throw new Error('场次不存在')
      const sold = s.total_slots - s.available_slots
      if (body.total_slots < sold) {
        throw new Error(`总名额不能小于已售数量（${sold}）`)
      }
      const delta = body.total_slots - s.total_slots
      s.total_slots = body.total_slots
      s.available_slots += delta
      if (s.available_slots > 0 && s.status === 'full') s.status = 'open'
      if (s.available_slots <= 0 && s.status === 'open') s.status = 'full'
      return { ...s }
    }

    const sessionStatusMatch = path.match(/^\/admin\/sessions\/([a-f0-9-]+)\/status$/)
    if (sessionStatusMatch) {
      verifyAdmin(headers)
      const s = sessions.find(s => s.id === sessionStatusMatch[1])
      if (!s) throw new Error('场次不存在')
      s.status = body.status
      return { ...s }
    }

    const sessionUpdateMatch = path.match(/^\/admin\/sessions\/([a-f0-9-]+)$/)
    if (sessionUpdateMatch) {
      verifyAdmin(headers)
      const s = sessions.find(s => s.id === sessionUpdateMatch[1])
      if (!s) throw new Error('场次不存在')
      if (body.title !== undefined) s.title = body.title
      if (body.description !== undefined) s.description = body.description
      if (body.coach !== undefined) s.coach = body.coach
      if (body.start_time !== undefined) s.start_time = body.start_time
      if (body.end_time !== undefined) s.end_time = body.end_time
      if (body.price !== undefined) s.price = body.price
      return { ...s }
    }

    const couponMatch = path.match(/^\/admin\/coupons\/([a-f0-9-]+)$/)
    if (couponMatch) {
      verifyAdmin(headers)
      const coupon = coupons.find(c => c.id === couponMatch[1])
      if (!coupon) throw new Error('优惠券不存在')
      coupon.status = body.status
      return { ...coupon }
    }
    throw new Error(`Not found: PATCH ${path}`)
  },

  exportCsv(headers?: Record<string, string>): string {
    verifyAdmin(headers)
    const header = '订单ID,学员姓名,学员年龄,家长姓名,家长电话,场次,教练,开始时间,结束时间,原价(分),优惠码,优惠金额(分),实付金额(分),订单状态,支付ID,支付时间,创建时间'
    const rows = orders.map(order => {
      const session = sessions.find(s => s.id === order.session_id)
      const payment = payments.find(p => p.order_id === order.id)
      return [
        order.id,
        order.student_name,
        order.student_age,
        order.parent_name,
        order.parent_phone,
        session?.title || '',
        session?.coach || '',
        session?.start_time || '',
        session?.end_time || '',
        order.original_amount,
        order.coupon_code || '',
        order.discount_amount,
        order.amount,
        order.status,
        payment?.payment_id || '',
        payment?.paid_at || '',
        order.created_at,
      ].join(',')
    })
    return [header, ...rows].join('\n')
  },

  forceExpireOrder(orderId: string) {
    const order = orders.find(o => o.id === orderId)
    if (order && order.status === 'pending') {
      order.status = 'expired'
      order.expire_at = new Date().toISOString()
      const session = sessions.find(s => s.id === order.session_id)
      if (session) {
        session.available_slots++
        if (session.status === 'full') session.status = 'open'
      }
      releaseCoupon(order.coupon_id)
    }
  },
}

function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
