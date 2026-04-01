import { createApp } from 'vue'
import App from './App.vue'

// Register service worker for offline support
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('Service Worker registration failed:', err)
    })
  })
}

// Request wake lock to prevent screen sleep
async function requestWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      const wakeLock = await (navigator as any).wakeLock.request('screen')
      // Re-acquire on visibility change (e.g. after screen was briefly off)
      document.addEventListener('visibilitychange', async () => {
        if (document.visibilityState === 'visible') {
          await (navigator as any).wakeLock.request('screen')
        }
      })
    }
  } catch (err) {
    console.warn('Wake Lock not available:', err)
  }
}

requestWakeLock()

createApp(App).mount('#app')
