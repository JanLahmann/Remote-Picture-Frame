/**
 * Photo sync composable.
 *
 * Periodically fetches new photos from the backend API and caches them locally.
 * Supports delta sync — only fetches photos uploaded since the last sync.
 */

import { ref, onMounted, onUnmounted } from 'vue'
import type { Photo } from '@/types'
import { syncPhotos } from '@/services/api'
import { cachePhotoBatch, pruneCache } from '@/services/cache'

export function useSync(syncIntervalMinutes: number = 5) {
  const photos = ref<Photo[]>([])
  const lastSyncedAt = ref<string | null>(null)
  const isSyncing = ref(false)
  const error = ref<string | null>(null)
  let intervalId: ReturnType<typeof setInterval> | null = null

  async function doSync() {
    if (isSyncing.value) return

    isSyncing.value = true
    error.value = null

    try {
      const result = await syncPhotos(lastSyncedAt.value || undefined)

      if (result.photos.length > 0) {
        // Merge new photos with existing ones (avoid duplicates)
        const existingIds = new Set(photos.value.map((p) => p.id))
        const newPhotos = result.photos.filter((p) => !existingIds.has(p.id))

        if (newPhotos.length > 0) {
          photos.value = [...newPhotos, ...photos.value]

          // Cache new photo images in background
          const urls = newPhotos
            .map((p) => p.download_url || p.thumbnail_url)
            .filter(Boolean)
          cachePhotoBatch(urls).then(() => pruneCache())
        }
      }

      lastSyncedAt.value = result.synced_at
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Sync failed'
      console.error('Photo sync failed:', err)
    } finally {
      isSyncing.value = false
    }
  }

  function startAutoSync() {
    stopAutoSync()
    intervalId = setInterval(doSync, syncIntervalMinutes * 60 * 1000)
  }

  function stopAutoSync() {
    if (intervalId) {
      clearInterval(intervalId)
      intervalId = null
    }
  }

  function updateInterval(minutes: number) {
    syncIntervalMinutes = minutes
    if (intervalId) {
      startAutoSync()
    }
  }

  onMounted(() => {
    doSync()
    startAutoSync()
  })

  onUnmounted(() => {
    stopAutoSync()
  })

  return {
    photos,
    lastSyncedAt,
    isSyncing,
    error,
    doSync,
    startAutoSync,
    stopAutoSync,
    updateInterval,
  }
}
