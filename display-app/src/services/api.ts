import type { SyncResponse, DisplaySettings } from '@/types'

// Configuration — set via environment variables at build time
const API_BASE = import.meta.env.VITE_API_BASE || ''
const DEVICE_TOKEN = import.meta.env.VITE_DEVICE_TOKEN || ''

function headers(): HeadersInit {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (DEVICE_TOKEN) {
    h['Authorization'] = `Bearer ${DEVICE_TOKEN}`
  }
  return h
}

export async function syncPhotos(since?: string): Promise<SyncResponse> {
  const params = new URLSearchParams({ action: 'sync' })
  if (since) params.set('since', since)

  const resp = await fetch(`${API_BASE}/display_sync_api?${params}`, {
    headers: headers(),
  })

  if (!resp.ok) {
    throw new Error(`Sync failed: ${resp.status} ${resp.statusText}`)
  }

  return resp.json()
}

export async function fetchSettings(): Promise<DisplaySettings> {
  const resp = await fetch(`${API_BASE}/display_sync_api?action=settings`, {
    headers: headers(),
  })

  if (!resp.ok) {
    throw new Error(`Settings fetch failed: ${resp.status}`)
  }

  return resp.json()
}
