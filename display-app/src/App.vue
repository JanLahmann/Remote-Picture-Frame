<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Slideshow from '@/components/Slideshow.vue'
import PhotoOverlay from '@/components/PhotoOverlay.vue'
import TouchControls from '@/components/TouchControls.vue'
import { useSync } from '@/composables/useSync'
import { useSlideshow } from '@/composables/useSlideshow'
import { useSettings } from '@/composables/useSettings'

// Settings (loaded from backend)
const { settings, nightBrightness } = useSettings()

// Photo sync
const { photos } = useSync(settings.value.sync_interval)

// Slideshow control
const { currentPhoto, currentIndex, totalPhotos, isPaused, orderedPhotos, next, previous, togglePause } =
  useSlideshow(photos, settings)

// Track previous photo for crossfade
const previousPhoto = ref(currentPhoto.value)
watch(currentPhoto, (_, old) => {
  previousPhoto.value = old
})

// Overlay control
const overlayRef = ref<InstanceType<typeof PhotoOverlay> | null>(null)

function showOverlay() {
  overlayRef.value?.show()
}

function hideOverlay() {
  overlayRef.value?.hide()
}

// Enter fullscreen on first interaction
function enterFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.().catch(() => {})
  }
}

// Night mode brightness filter
const brightnessFilter = computed(() => `brightness(${nightBrightness.value})`)
</script>

<template>
  <div class="app" :style="{ filter: brightnessFilter }" @click.once="enterFullscreen">
    <Slideshow
      :photo="currentPhoto"
      :previous-photo="previousPhoto"
      :settings="settings"
    />

    <PhotoOverlay
      ref="overlayRef"
      :photo="currentPhoto"
      :settings="settings"
      :is-paused="isPaused"
      :current-index="currentIndex"
      :total-photos="totalPhotos"
    />

    <TouchControls
      @next="next"
      @previous="previous"
      @toggle-pause="togglePause"
      @show-overlay="showOverlay"
      @hide-overlay="hideOverlay"
    />
  </div>
</template>

<style>
/* Global styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #000;
  cursor: none; /* Hide cursor on picture frame */
  user-select: none;
  -webkit-user-select: none;
}

.app {
  width: 100%;
  height: 100%;
  transition: filter 2s ease;
}
</style>
