<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { Photo, DisplaySettings } from '@/types'

const props = defineProps<{
  photo: Photo | null
  settings: DisplaySettings
  isPaused: boolean
  currentIndex: number
  totalPhotos: number
}>()

const visible = ref(false)
let hideTimer: ReturnType<typeof setTimeout> | null = null

// Show overlay briefly when photo changes
watch(
  () => props.photo?.id,
  () => {
    if (!props.settings.show_overlay || !props.photo) return

    visible.value = true

    if (hideTimer) clearTimeout(hideTimer)

    if (props.settings.overlay_duration > 0) {
      hideTimer = setTimeout(() => {
        visible.value = false
      }, props.settings.overlay_duration * 1000)
    }
  },
)

function show() {
  visible.value = true
  if (hideTimer) clearTimeout(hideTimer)
}

function hide() {
  visible.value = false
}

const formattedDate = computed(() => {
  if (!props.photo?.date_taken) return ''
  try {
    const d = new Date(props.photo.date_taken)
    return d.toLocaleDateString('de-DE', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
  } catch {
    return ''
  }
})

const locationName = computed(() => {
  const loc = props.photo?.location
  if (!loc) return ''
  if (loc.name) return loc.name
  // Fallback: show rounded coordinates
  if (loc.lat && loc.lon) return `${loc.lat.toFixed(2)}, ${loc.lon.toFixed(2)}`
  return ''
})

defineExpose({ show, hide })
</script>

<template>
  <Transition name="overlay">
    <div v-if="visible && photo" class="overlay">
      <div class="overlay-content">
        <!-- Caption -->
        <h2 v-if="photo.caption" class="caption">{{ photo.caption }}</h2>

        <!-- Description -->
        <p v-if="photo.description" class="description">{{ photo.description }}</p>

        <!-- Meta line: date, location, uploader -->
        <div class="meta">
          <span v-if="formattedDate" class="meta-item">
            {{ formattedDate }}
          </span>
          <span v-if="locationName" class="meta-item">
            {{ locationName }}
          </span>
          <span v-if="photo.uploaded_by" class="meta-item">
            von {{ photo.uploaded_by }}
          </span>
        </div>

        <!-- Progress / status -->
        <div class="status">
          <span v-if="isPaused" class="paused-indicator">⏸ Pausiert</span>
          <span class="counter">{{ currentIndex + 1 }} / {{ totalPhotos }}</span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.overlay {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.75));
  padding: 3rem 2rem 1.5rem;
  color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  z-index: 10;
  pointer-events: none;
}

.overlay-content {
  max-width: 80%;
}

.caption {
  font-size: 1.6rem;
  font-weight: 600;
  margin: 0 0 0.3rem;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
}

.description {
  font-size: 1.1rem;
  margin: 0 0 0.5rem;
  opacity: 0.9;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.meta {
  display: flex;
  gap: 1.5rem;
  font-size: 0.95rem;
  opacity: 0.8;
}

.meta-item {
  white-space: nowrap;
}

.status {
  position: fixed;
  bottom: 1rem;
  right: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.85rem;
  opacity: 0.6;
}

.paused-indicator {
  opacity: 0.9;
}

/* Transition */
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
  transform: translateY(1rem);
}
</style>
