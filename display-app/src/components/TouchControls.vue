<script setup lang="ts">
/**
 * Invisible touch control layer.
 *
 * - Tap left edge: previous photo
 * - Tap right edge: next photo
 * - Double tap: pause/resume
 * - Swipe up: show overlay
 * - Swipe down: hide overlay
 */

import { ref } from 'vue'

const emit = defineEmits<{
  next: []
  previous: []
  togglePause: []
  showOverlay: []
  hideOverlay: []
  favorite: []
}>()

const touchStartX = ref(0)
const touchStartY = ref(0)
const touchStartTime = ref(0)
let lastTapTime = 0
let longPressTimer: ReturnType<typeof setTimeout> | null = null
let longPressTriggered = false

function onTouchStart(e: TouchEvent) {
  const touch = e.touches[0]
  touchStartX.value = touch.clientX
  touchStartY.value = touch.clientY
  touchStartTime.value = Date.now()
  longPressTriggered = false

  // Long press detection (800ms)
  longPressTimer = setTimeout(() => {
    longPressTriggered = true
    emit('favorite')
  }, 800)
}

function onTouchEnd(e: TouchEvent) {
  if (longPressTimer) {
    clearTimeout(longPressTimer)
    longPressTimer = null
  }
  if (longPressTriggered) return // Already handled by long press

  const touch = e.changedTouches[0]
  const dx = touch.clientX - touchStartX.value
  const dy = touch.clientY - touchStartY.value
  const dt = Date.now() - touchStartTime.value

  const absDx = Math.abs(dx)
  const absDy = Math.abs(dy)

  // Swipe detection (minimum 50px, within 500ms)
  if (Math.max(absDx, absDy) > 50 && dt < 500) {
    if (absDy > absDx) {
      // Vertical swipe
      if (dy < 0) {
        emit('showOverlay')
      } else {
        emit('hideOverlay')
      }
      return
    }
  }

  // Tap detection (minimal movement, within 300ms)
  if (absDx < 20 && absDy < 20 && dt < 300) {
    const now = Date.now()

    // Double tap detection
    if (now - lastTapTime < 400) {
      emit('togglePause')
      lastTapTime = 0
      return
    }

    lastTapTime = now

    // Single tap — wait to distinguish from double tap
    setTimeout(() => {
      if (lastTapTime === 0) return // Was a double tap

      const screenWidth = window.innerWidth
      const tapX = touch.clientX

      if (tapX < screenWidth * 0.3) {
        emit('previous')
      } else if (tapX > screenWidth * 0.7) {
        emit('next')
      } else {
        // Center tap — show overlay
        emit('showOverlay')
      }
    }, 420)
  }
}
</script>

<template>
  <div
    class="touch-layer"
    @touchstart.passive="onTouchStart"
    @touchend.passive="onTouchEnd"
  />
</template>

<style scoped>
.touch-layer {
  position: fixed;
  inset: 0;
  z-index: 20;
  /* Invisible but captures all touch events */
}
</style>
