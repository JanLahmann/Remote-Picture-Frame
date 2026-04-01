/**
 * Service Worker for FamilyFrame PWA.
 *
 * Caching strategy:
 * - App shell (HTML, JS, CSS): Cache-first with network fallback
 * - Photos: Cache-first (photos are cached proactively by the app)
 * - API calls: Network-first with no caching (always get fresh data)
 */

const APP_CACHE = 'familyframe-app-v1'
const PHOTO_CACHE = 'familyframe-photos-v1'

// App shell files to pre-cache on install
const APP_SHELL = [
  '/',
  '/index.html',
  '/manifest.json',
]

// Install: pre-cache app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(APP_CACHE).then((cache) => {
      return cache.addAll(APP_SHELL)
    })
  )
  // Activate immediately
  self.skipWaiting()
})

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== APP_CACHE && key !== PHOTO_CACHE)
          .map((key) => caches.delete(key))
      )
    })
  )
  // Take control of all clients immediately
  self.clients.claim()
})

// Fetch: route requests to appropriate strategy
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)

  // API calls: network only (sync must be fresh)
  if (url.pathname.includes('display_sync_api') || url.pathname.includes('/api/')) {
    event.respondWith(fetch(event.request))
    return
  }

  // Photo images: cache-first
  if (isPhotoRequest(event.request)) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        return cached || fetch(event.request).then((response) => {
          if (response.ok) {
            const clone = response.clone()
            caches.open(PHOTO_CACHE).then((cache) => cache.put(event.request, clone))
          }
          return response
        })
      })
    )
    return
  }

  // App shell: cache-first, network fallback
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        if (response.ok && event.request.method === 'GET') {
          const clone = response.clone()
          caches.open(APP_CACHE).then((cache) => cache.put(event.request, clone))
        }
        return response
      })
    })
  )
})

function isPhotoRequest(request) {
  const url = request.url.toLowerCase()
  return (
    url.includes('thumbnail') ||
    url.includes('.jpg') ||
    url.includes('.jpeg') ||
    url.includes('.png') ||
    url.includes('.webp') ||
    url.includes('graph.microsoft.com') ||
    url.includes('sharepoint.com')
  )
}
