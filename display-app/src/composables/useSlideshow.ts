/**
 * Slideshow state machine composable.
 *
 * Manages the current photo index, auto-advancement timer,
 * and display order with smart rotation:
 * - Weighted random: newer photos shown more often
 * - Repeat avoidance: no photo within last N shown
 * - New photo priority: photos < 24h old get higher weight
 * - Auto-resume: paused slideshow resumes after 5 minutes
 */

import { ref, computed, watch, onUnmounted } from 'vue'
import type { Photo, DisplaySettings } from '@/types'

const AUTO_RESUME_MS = 5 * 60 * 1000 // 5 minutes
const RECENTLY_SHOWN_SIZE = 20 // avoid repeating last N photos

export function useSlideshow(
  photos: ReturnType<typeof ref<Photo[]>>,
  settings: ReturnType<typeof ref<DisplaySettings>>,
) {
  const currentIndex = ref(0)
  const isPaused = ref(false)
  let timerId: ReturnType<typeof setTimeout> | null = null
  let autoResumeTimerId: ReturnType<typeof setTimeout> | null = null

  // Track recently shown photo IDs to avoid repeats
  const recentlyShown = ref<string[]>([])

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

  /** Pick the next photo using smart weighted selection (for random mode). */
  function pickSmartNext(): number {
    const list = orderedPhotos.value
    if (list.length <= 1) return 0

    const now = Date.now()
    const oneDayAgo = now - 24 * 60 * 60 * 1000
    const recentSet = new Set(recentlyShown.value)

    const today = new Date()
    const todayMMDD = `${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

    // Check if it's someone's birthday
    const birthdayNames = new Set(
      (settings.value.birthdays || [])
        .filter((b) => b.date === todayMMDD)
        .map((b) => b.name),
    )

    // Build weights for each photo
    const weights: number[] = list.map((photo) => {
      // Base weight
      let w = 1.0

      // Boost new photos (uploaded < 24h ago)
      const uploadedAt = new Date(photo.uploaded_at).getTime()
      if (uploadedAt > oneDayAgo) {
        w *= 3.0
      }

      // Boost newer photos slightly (age-based decay)
      const ageMs = now - uploadedAt
      const ageDays = ageMs / (1000 * 60 * 60 * 24)
      if (ageDays < 7) {
        w *= 2.0
      } else if (ageDays < 30) {
        w *= 1.5
      }

      // Boost favorites
      if (photo.favorite) {
        w *= 2.5
      }

      // Boost "on this day" photos (same month+day from previous years)
      if (photo.date_taken) {
        try {
          const taken = new Date(photo.date_taken)
          const takenMMDD = `${String(taken.getMonth() + 1).padStart(2, '0')}-${String(taken.getDate()).padStart(2, '0')}`
          if (takenMMDD === todayMMDD && taken.getFullYear() < today.getFullYear()) {
            w *= 4.0 // Strong boost for memories
          }
        } catch { /* ignore invalid dates */ }
      }

      // Boost birthday person's photos
      if (birthdayNames.size > 0) {
        const photoPeople = photo.people || []
        const isFromBirthdayPerson = birthdayNames.has(photo.uploaded_by)
        const hasBirthdayPerson = photoPeople.some((p) => birthdayNames.has(p))
        if (isFromBirthdayPerson || hasBirthdayPerson) {
          w *= 3.0
        }
      }

      // Penalize recently shown photos
      if (recentSet.has(photo.id)) {
        w *= 0.05
      }

      return w
    })

    // Weighted random selection
    const totalWeight = weights.reduce((sum, w) => sum + w, 0)
    let r = Math.random() * totalWeight
    for (let i = 0; i < weights.length; i++) {
      r -= weights[i]
      if (r <= 0) return i
    }
    return list.length - 1
  }

  function trackShown(photo: Photo | null) {
    if (!photo) return
    const recent = recentlyShown.value
    if (recent[recent.length - 1] === photo.id) return // already tracked
    recent.push(photo.id)
    if (recent.length > RECENTLY_SHOWN_SIZE) {
      recent.shift()
    }
  }

  function next() {
    if (orderedPhotos.value.length === 0) return

    if (settings.value.order === 'random') {
      currentIndex.value = pickSmartNext()
    } else {
      currentIndex.value = (currentIndex.value + 1) % orderedPhotos.value.length
    }

    trackShown(currentPhoto.value)
    scheduleNext()
  }

  function previous() {
    if (orderedPhotos.value.length === 0) return
    const len = orderedPhotos.value.length
    currentIndex.value = (currentIndex.value - 1 + len) % len
    trackShown(currentPhoto.value)
    scheduleNext()
  }

  function togglePause() {
    isPaused.value = !isPaused.value
    if (isPaused.value) {
      clearTimer()
      startAutoResume()
    } else {
      clearAutoResume()
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

  // Auto-resume: unpause after 5 minutes
  function startAutoResume() {
    clearAutoResume()
    autoResumeTimerId = setTimeout(() => {
      if (isPaused.value) {
        isPaused.value = false
        scheduleNext()
      }
    }, AUTO_RESUME_MS)
  }

  function clearAutoResume() {
    if (autoResumeTimerId) {
      clearTimeout(autoResumeTimerId)
      autoResumeTimerId = null
    }
  }

  // Start slideshow when photos are available
  watch(
    () => orderedPhotos.value.length,
    (len) => {
      if (len > 0 && !isPaused.value) {
        trackShown(currentPhoto.value)
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

  onUnmounted(() => {
    clearTimer()
    clearAutoResume()
  })

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
