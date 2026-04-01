/**
 * Photo cache management using the Cache Storage API.
 *
 * Caches photo images locally so the slideshow works offline.
 * Manages cache size to avoid filling up device storage.
 */

const PHOTO_CACHE = 'familyframe-photos-v1'
const MAX_CACHED_PHOTOS = 500

export async function getCachedPhoto(url: string): Promise<Response | undefined> {
  const cache = await caches.open(PHOTO_CACHE)
  return cache.match(url) || undefined
}

export async function cachePhoto(url: string): Promise<void> {
  if (!url) return
  const cache = await caches.open(PHOTO_CACHE)

  // Skip if already cached
  const existing = await cache.match(url)
  if (existing) return

  try {
    const response = await fetch(url, { mode: 'cors' })
    if (response.ok) {
      await cache.put(url, response)
    }
  } catch (err) {
    console.warn('Failed to cache photo:', url, err)
  }
}

export async function cachePhotoBatch(urls: string[]): Promise<void> {
  // Cache photos in batches to avoid overwhelming the network
  const batchSize = 3
  for (let i = 0; i < urls.length; i += batchSize) {
    const batch = urls.slice(i, i + batchSize)
    await Promise.allSettled(batch.map((url) => cachePhoto(url)))
  }
}

export async function pruneCache(): Promise<void> {
  const cache = await caches.open(PHOTO_CACHE)
  const keys = await cache.keys()

  if (keys.length > MAX_CACHED_PHOTOS) {
    // Remove oldest entries (first in the list)
    const toRemove = keys.slice(0, keys.length - MAX_CACHED_PHOTOS)
    await Promise.all(toRemove.map((key) => cache.delete(key)))
  }
}

export async function getCacheSize(): Promise<{ count: number; bytes: number }> {
  const cache = await caches.open(PHOTO_CACHE)
  const keys = await cache.keys()

  let bytes = 0
  for (const key of keys) {
    const response = await cache.match(key)
    if (response) {
      const blob = await response.clone().blob()
      bytes += blob.size
    }
  }

  return { count: keys.length, bytes }
}
