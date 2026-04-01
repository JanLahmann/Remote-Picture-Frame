/**
 * Slideshow state machine composable.
 *
 * Manages the current photo index, auto-advancement timer,
 * and display order (random, newest first, chronological).
 */

import { ref, computed, watch, onUnmounted } from 'vue'
import type { Photo, DisplaySettings } from '@/types'

export function useSlideshow(
  photos: ReturnType<typeof ref<Photo[]>>,
  settings: ReturnType<typeof ref<DisplaySettings>>,
) {
  const currentIndex = ref(0)
  const isPaused = ref(false)
  let timerId: ReturnType<typeof setTimeout> | null = null

  // Ordered photo list based on settings
  const orderedPhotos = computed<Photo[]>(() => {
    const list = [...photos.value]
    if (list.length === 0) return []

    switch (settings.value.order) {
      case 'newest':
        return list.sort(
          (a, b) => new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime(),
        )
      case 'chronological':
        return list.sort((a, b) => {
          const da = a.date_taken || a.uploaded_at
          const db = b.date_taken || b.uploaded_at
          return new Date(da).getTime() - new Date(db).getTime()
        })
      case 'random':
      default:
        // Fisher-Yates shuffle
        for (let i = list.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1))
          ;[list[i], list[j]] = [list[j], list[i]]
        }
        return list
    }
  })

  const currentPhoto = computed<Photo | null>(() => {
    const list = orderedPhotos.value
    if (list.length === 0) return null
    return list[currentIndex.value % list.length] || null
  })

  const totalPhotos = computed(() => photos.value.length)

  function next() {
    if (orderedPhotos.value.length === 0) return
    currentIndex.value = (currentIndex.value + 1) % orderedPhotos.value.length
    scheduleNext()
  }

  function previous() {
    if (orderedPhotos.value.length === 0) return
    const len = orderedPhotos.value.length
    currentIndex.value = (currentIndex.value - 1 + len) % len
    scheduleNext()
  }

  function togglePause() {
    isPaused.value = !isPaused.value
    if (isPaused.value) {
      clearTimer()
    } else {
      scheduleNext()
    }
  }

  function scheduleNext() {
    clearTimer()
    if (isPaused.value || orderedPhotos.value.length <= 1) return

    timerId = setTimeout(() => {
      next()
    }, settings.value.slideshow_interval * 1000)
  }

  function clearTimer() {
    if (timerId) {
      clearTimeout(timerId)
      timerId = null
    }
  }

  // Start slideshow when photos are available
  watch(
    () => orderedPhotos.value.length,
    (len) => {
      if (len > 0 && !isPaused.value) {
        scheduleNext()
      }
    },
  )

  // Restart timer when interval changes
  watch(
    () => settings.value.slideshow_interval,
    () => {
      if (!isPaused.value) scheduleNext()
    },
  )

  onUnmounted(() => clearTimer())

  return {
    currentPhoto,
    currentIndex,
    totalPhotos,
    isPaused,
    orderedPhotos,
    next,
    previous,
    togglePause,
  }
}
