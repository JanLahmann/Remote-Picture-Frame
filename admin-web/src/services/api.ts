const API_BASE = import.meta.env.VITE_API_BASE || ''
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN || ''

function headers(): HeadersInit {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (ADMIN_TOKEN) h['Authorization'] = `Bearer ${ADMIN_TOKEN}`
  return h
}

async function request(action: string, params: Record<string, string> = {}, body?: unknown) {
  const qs = new URLSearchParams({ action, ...params })
  const opts: RequestInit = { headers: headers() }

  if (body) {
    opts.method = 'POST'
    opts.body = JSON.stringify(body)
  }

  const resp = await fetch(`${API_BASE}/admin_api?${qs}`, opts)
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.error || `Request failed: ${resp.status}`)
  return data
}

export async function listPhotos(limit = 50) {
  return request('list', { limit: String(limit) })
}

export async function getPhoto(id: string) {
  return request('get', { id })
}

export async function updatePhoto(id: string, updates: Record<string, unknown>) {
  return request('update', { id }, updates)
}

export async function toggleVisibility(id: string) {
  return request('visibility', { id }, {})
}

export async function deletePhoto(id: string) {
  return request('delete', { id }, {})
}

export async function getStats() {
  return request('stats')
}

export async function getSettings() {
  return request('settings')
}

export async function updateSettings(settings: Record<string, unknown>) {
  return request('settings', {}, settings)
}
