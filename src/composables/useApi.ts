import { ref } from 'vue'
import { mockApi } from '@/mock'

const API_BASE = import.meta.env.VITE_API_URL || '/api'
const USE_MOCK = !import.meta.env.VITE_API_URL

async function realRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export function useApi() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function get<T>(path: string, headers?: Record<string, string>): Promise<T> {
    loading.value = true
    error.value = null
    try {
      if (USE_MOCK) {
        return (await mockApi.get(path, headers)) as T
      }
      return await realRequest<T>(path, { headers })
    } catch (e: any) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function post<T>(path: string, body?: any, headers?: Record<string, string>): Promise<T> {
    loading.value = true
    error.value = null
    try {
      if (USE_MOCK) {
        return (await mockApi.post(path, body, headers)) as T
      }
      return await realRequest<T>(path, {
        method: 'POST',
        headers,
        body: body ? JSON.stringify(body) : undefined,
      })
    } catch (e: any) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function patch<T>(path: string, body?: any, headers?: Record<string, string>): Promise<T> {
    loading.value = true
    error.value = null
    try {
      if (USE_MOCK) {
        return (await mockApi.patch(path, body, headers)) as T
      }
      return await realRequest<T>(path, {
        method: 'PATCH',
        headers,
        body: body ? JSON.stringify(body) : undefined,
      })
    } catch (e: any) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function download(path: string, filename: string, headers?: Record<string, string>) {
    loading.value = true
    error.value = null
    try {
      if (USE_MOCK) {
        const csv = mockApi.exportCsv(headers)
        const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        a.click()
        URL.revokeObjectURL(url)
        return
      }
      const res = await fetch(`${API_BASE}${path}`, { headers: { ...headers } })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch (e: any) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  return { loading, error, get, post, patch, download }
}
