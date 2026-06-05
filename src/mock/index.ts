function genId(): string {
  return crypto.randomUUID()
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
  expire_at: string
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

const ADMIN_SECRET = 'changeme'

const sessions: MockSession[] = [
  {
    id: 'a0000000-0000-0000-0000-000000000001',
    title: '亲子启蒙班 A',
    description: '适合 1-3 岁宝宝，家长陪同入水',
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
    description: '适合 1-3 岁宝宝，家长陪同入水',
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
    description: '适合 3-6 岁儿童，学习基础泳姿',
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
    description: '适合 6-12 岁少儿，提升游泳技巧',
    coach: '赵教练',
    start_time: '2026-07-03T14:00:00',
    end_time: '2026-07-03T16:00:00',
    total_slots: 12,
    available_slots: 12,
    price: 29900,
    status: 'open',
  },
]

const orders: MockOrder[] = []
const payments: MockPayment[] = []

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

    if (path === '/sessions') {
      return sessions.map(s => ({ ...s }))
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
        total_revenue: orders.filter(o => o.status === 'paid').reduce((sum, o) => sum + o.amount, 0),
      }
    }

    if (path.startsWith('/admin/orders')) {
      verifyAdmin(headers)
      const urlObj = new URL(path, 'http://localhost')
      const status = urlObj.searchParams.get('status')
      let result = orders.map(o => ({ ...o }))
      if (status) result = result.filter(o => o.status === status)
      return result.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
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
        payment_id: payment.payment_id,
        paid_at: payment.paid_at,
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

  async post(path: string, body?: any): Promise<any> {
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
        amount: session.price,
        expire_at: expireAt.toISOString(),
        created_at: new Date().toISOString(),
      }
      orders.push(order)
      return { ...order }
    }

    if (path === '/payments/create') {
      const order = orders.find(o => o.id === body.order_id)
      if (!order) throw new Error('订单不存在')
      if (order.status !== 'pending') throw new Error('订单状态不可支付')
      if (new Date(order.expire_at).getTime() < Date.now()) {
        order.status = 'expired'
        const session = sessions.find(s => s.id === order.session_id)
        if (session) { session.available_slots++; if (session.status === 'full') session.status = 'open' }
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
        throw new Error('订单已过期，名额已释放')
      }

      const payment = payments.find(p => p.order_id === body.order_id)
      if (payment) {
        payment.status = 'paid'
        payment.paid_at = new Date().toISOString()
      }
      order.status = 'paid'
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

    throw new Error(`Not found: POST ${path}`)
  },

  exportCsv(headers?: Record<string, string>): string {
    verifyAdmin(headers)
    const header = '订单ID,学员姓名,学员年龄,家长姓名,家长电话,场次,教练,开始时间,结束时间,金额(分),订单状态,支付ID,支付时间,创建时间'
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
    }
  },
}

function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
