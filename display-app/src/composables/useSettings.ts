/**
 * Remote settings composable.
 *
 * Fetches display settings from the backend API and applies them.
 * Includes night mode logic (CSS brightness dimming on schedule).
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { DisplaySettings } from '@/types'
import { DEFAULT_SETTINGS } from '@/types'
import { fetchSettings } from '@/services/api'

export function useSettings() {
  const settings = ref<DisplaySettings>({ ...DEFAULT_SETTINGS })
  const isNightMode = ref(false)
  let settingsTimer: ReturnType<typeof setInterval> | null = null
  let nightModeTimer: ReturnType<typeof setInterval> | null = null

  async function loadSettings() {
    try {
      const remote = await fetchSettings()
      settings.value = { ...DEFAULT_SETTINGS, ...remote }
    } catch (err) {
      console.warn('Failed to load remote settings, using defaults:', err)
    }
  }

  function checkNightMode() {
    const nm = settings.value.night_mode
    if (!nm.enabled) {
      isNightMode.value = false
      return
    }

    const now = new Date()
    const currentMinutes = now.getHours() * 60 + now.getMinutes()

    const [startH, startM] = nm.dim_start.split(':').map(Number)
    const [endH, endM] = nm.dim_end.split(':').map(Number)
    const startMinutes = startH * 60 + startM
    const endMinutes = endH * 60 + endM

    if (startMinutes > endMinutes) {
      // Crosses midnight (e.g. 22:00 - 07:00)
      isNightMode.value = currentMinutes >= startMinutes || currentMinutes < endMinutes
    } else {
      isNightMode.value = currentMinutes >= startMinutes && currentMinutes < endMinutes
    }
  }

  const nightBrightness = computed(() => {
    if (isNightMode.value) {
      return settings.value.night_mode.brightness
    }
    return 1
  })

  onMounted(() => {
    loadSettings()
    checkNightMode()

    // Refresh settings every 10 minutes
    settingsTimer = setInterval(loadSettings, 10 * 60 * 1000)
    // Check night mode every minute
    nightModeTimer = setInterval(checkNightMode, 60 * 1000)
  })

  onUnmounted(() => {
    if (settingsTimer) clearInterval(settingsTimer)
    if (nightModeTimer) clearInterval(nightModeTimer)
  })

  return {
    settings,
    isNightMode,
    nightBrightness,
    loadSettings,
  }
}
