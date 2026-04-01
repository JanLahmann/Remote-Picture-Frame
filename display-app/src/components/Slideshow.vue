<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Photo, DisplaySettings } from '@/types'

const props = defineProps<{
  photo: Photo | null
  previousPhoto: Photo | null
  settings: DisplaySettings
}>()

// Track which image slot is active for crossfade
const showSlotA = ref(true)
const slotAUrl = ref('')
const slotBUrl = ref('')

// Ken Burns animation state
const kenBurnsClass = ref('kb-1')
const kenBurnsClasses = ['kb-1', 'kb-2', 'kb-3', 'kb-4']
let kenBurnsIndex = 0

watch(
  () => props.photo?.id,
  () => {
    if (!props.photo) return

    const url = props.photo.download_url || props.photo.thumbnail_url
    if (!url) return

    // Crossfade: load new image into the inactive slot, then switch
    if (showSlotA.value) {
      slotBUrl.value = url
    } else {
      slotAUrl.value = url
    }
    showSlotA.value = !showSlotA.value

    // Cycle Ken Burns animation
    if (props.settings.transition === 'kenburns') {
      kenBurnsIndex = (kenBurnsIndex + 1) % kenBurnsClasses.length
      kenBurnsClass.value = kenBurnsClasses[kenBurnsIndex]
    }
  },
)

// Initialize first photo
watch(
  () => props.photo?.download_url || props.photo?.thumbnail_url,
  (url) => {
    if (url && !slotAUrl.value && !slotBUrl.value) {
      slotAUrl.value = url
      showSlotA.value = true
    }
  },
  { immediate: true },
)

const transitionDuration = computed(() => `${props.settings.transition_duration}s`)
const isKenBurns = computed(() => props.settings.transition === 'kenburns')
const slideshowDuration = computed(() => `${props.settings.slideshow_interval}s`)
</script>

<template>
  <div class="slideshow">
    <!-- Image Slot A -->
    <div
      class="slide"
      :class="[
        { active: showSlotA, 'ken-burns': isKenBurns },
        isKenBurns && showSlotA ? kenBurnsClass : '',
      ]"
    >
      <img
        v-if="slotAUrl"
        :src="slotAUrl"
        alt=""
        draggable="false"
      />
    </div>

    <!-- Image Slot B -->
    <div
      class="slide"
      :class="[
        { active: !showSlotA, 'ken-burns': isKenBurns },
        isKenBurns && !showSlotA ? kenBurnsClass : '',
      ]"
    >
      <img
        v-if="slotBUrl"
        :src="slotBUrl"
        alt=""
        draggable="false"
      />
    </div>

    <!-- Loading state -->
    <div v-if="!photo" class="loading">
      <p>Lade Fotos...</p>
    </div>
  </div>
</template>

<style scoped>
.slideshow {
  position: fixed;
  inset: 0;
  background: #000;
  overflow: hidden;
}

.slide {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity v-bind(transitionDuration) ease-in-out;
  display: flex;
  align-items: center;
  justify-content: center;
}

.slide.active {
  opacity: 1;
}

.slide img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  user-select: none;
  -webkit-user-drag: none;
}

/* Ken Burns effect — gentle zoom and pan animations */
.slide.ken-burns img {
  max-width: none;
  max-height: none;
  width: 110%;
  height: 110%;
  object-fit: cover;
}

.slide.ken-burns.kb-1 img {
  animation: kb1 v-bind(slideshowDuration) ease-in-out forwards;
}
.slide.ken-burns.kb-2 img {
  animation: kb2 v-bind(slideshowDuration) ease-in-out forwards;
}
.slide.ken-burns.kb-3 img {
  animation: kb3 v-bind(slideshowDuration) ease-in-out forwards;
}
.slide.ken-burns.kb-4 img {
  animation: kb4 v-bind(slideshowDuration) ease-in-out forwards;
}

@keyframes kb1 {
  from { transform: scale(1) translate(0, 0); }
  to { transform: scale(1.15) translate(-2%, -1%); }
}
@keyframes kb2 {
  from { transform: scale(1.1) translate(-2%, -1%); }
  to { transform: scale(1) translate(1%, 1%); }
}
@keyframes kb3 {
  from { transform: scale(1) translate(1%, 0); }
  to { transform: scale(1.12) translate(-1%, 2%); }
}
@keyframes kb4 {
  from { transform: scale(1.1) translate(0, 1%); }
  to { transform: scale(1) translate(0, -1%); }
}

.loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 1.5rem;
}
</style>
