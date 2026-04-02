<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import Slideshow from '@/components/Slideshow.vue'
import PhotoOverlay from '@/components/PhotoOverlay.vue'
import TouchControls from '@/components/TouchControls.vue'
import PersonFilter from '@/components/PersonFilter.vue'
import { useSync } from '@/composables/useSync'
import { useSlideshow } from '@/composables/useSlideshow'
import { useSettings } from '@/composables/useSettings'
import type { Photo } from '@/types'

// Settings (loaded from backend)
const { settings, nightBrightness } = useSettings()

// Photo sync
const { photos } = useSync(settings.value.sync_interval)

// Person filter: filter displayed photos by uploader
const activeFilter = ref('')
const filteredPhotos = computed(() => {
  if (!activeFilter.value) return photos.value
  return photos.value.filter((p) => p.uploaded_by === activeFilter.value)
})

// Count of new photos (uploaded in last 24h)
const newPhotoCount = computed(() => {
  const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000
  return photos.value.filter(
    (p) => new Date(p.uploaded_at).getTime() > oneDayAgo,
  ).length
})

// Slideshow control (uses filtered photos)
const { currentPhoto, currentIndex, totalPhotos, isPaused, orderedPhotos, next, previous, togglePause } =
  useSlideshow(filteredPhotos, settings)

// Track previous photo for crossfade
const previousPhoto = ref<Photo | null>(currentPhoto.value)
watch(currentPhoto, (_, old) => {
  previousPhoto.value = old
})

// Overlay control
const overlayRef = ref<InstanceType<typeof PhotoOverlay> | null>(null)
const personFilterRef = ref<InstanceType<typeof PersonFilter> | null>(null)

function showOverlay() {
  overlayRef.value?.show()
}

function hideOverlay() {
  overlayRef.value?.hide()
}

function onTogglePause() {
  togglePause()
  // Show person filter when pausing (double-tap)
  if (isPaused.value) {
    personFilterRef.value?.show()
  } else {
    personFilterRef.value?.hide()
  }
}

function onPersonFilter(uploader: string) {
  activeFilter.value = uploader
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
      :new-photo-count="newPhotoCount"
      :active-filter="activeFilter"
    />

    <PersonFilter
      ref="personFilterRef"
      @filter="onPersonFilter"
    />

    <TouchControls
      @next="next"
      @previous="previous"
      @toggle-pause="onTogglePause"
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
