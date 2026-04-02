<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { fetchUploaders } from '@/services/api'

const emit = defineEmits<{
  filter: [uploader: string]
}>()

const uploaders = ref<string[]>([])
const visible = ref(false)
const activeFilter = ref('')
let autoResetTimer: ReturnType<typeof setTimeout> | null = null
let hideTimer: ReturnType<typeof setTimeout> | null = null

const AUTO_RESET_MS = 30 * 60 * 1000 // 30 minutes

async function loadUploaders() {
  try {
    uploaders.value = await fetchUploaders()
  } catch {
    uploaders.value = []
  }
}

function show() {
  if (uploaders.value.length === 0) return
  visible.value = true
  // Auto-hide after 8 seconds if no selection
  clearHideTimer()
  hideTimer = setTimeout(() => {
    if (visible.value && !activeFilter.value) {
      visible.value = false
    }
  }, 8000)
}

function hide() {
  visible.value = false
  clearHideTimer()
}

function selectUploader(name: string) {
  clearHideTimer()
  clearAutoReset()

  if (activeFilter.value === name) {
    // Deselect — back to all photos
    activeFilter.value = ''
    emit('filter', '')
    visible.value = false
  } else {
    activeFilter.value = name
    emit('filter', name)
    visible.value = false

    // Auto-reset filter after 30 minutes
    autoResetTimer = setTimeout(() => {
      activeFilter.value = ''
      emit('filter', '')
    }, AUTO_RESET_MS)
  }
}

function showAll() {
  clearAutoReset()
  activeFilter.value = ''
  emit('filter', '')
  visible.value = false
}

function clearHideTimer() {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
}

function clearAutoReset() {
  if (autoResetTimer) {
    clearTimeout(autoResetTimer)
    autoResetTimer = null
  }
}

onMounted(loadUploaders)
onUnmounted(() => {
  clearHideTimer()
  clearAutoReset()
})

defineExpose({ show, hide, visible, activeFilter })
</script>

<template>
  <Transition name="filter-panel">
    <div v-if="visible" class="person-filter">
      <div class="filter-buttons">
        <button
          v-if="activeFilter"
          class="filter-btn all-btn"
          @click="showAll"
        >
          Alle Fotos
        </button>
        <button
          v-for="name in uploaders"
          :key="name"
          :class="['filter-btn', { active: activeFilter === name }]"
          @click="selectUploader(name)"
        >
          {{ name }}
        </button>
      </div>
      <div v-if="activeFilter" class="active-hint">
        Zeige nur Fotos von {{ activeFilter }}
      </div>
    </div>
  </Transition>

  <!-- Small persistent indicator when filter is active but panel is hidden -->
  <Transition name="badge">
    <div v-if="!visible && activeFilter" class="filter-badge" @click="show">
      {{ activeFilter }}
    </div>
  </Transition>
</template>

<style scoped>
.person-filter {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 15;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  pointer-events: auto;
}

.filter-buttons {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
  max-width: 80vw;
}

.filter-btn {
  padding: 0.8rem 1.5rem;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 2rem;
  color: #fff;
  font-size: 1.2rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.filter-btn:hover,
.filter-btn:active {
  background: rgba(78, 204, 163, 0.5);
  border-color: rgba(78, 204, 163, 0.8);
}

.filter-btn.active {
  background: rgba(78, 204, 163, 0.6);
  border-color: #4ecca3;
}

.all-btn {
  border-color: rgba(255, 255, 255, 0.5);
  font-size: 1rem;
}

.active-hint {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.filter-badge {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 12;
  padding: 0.4rem 0.8rem;
  background: rgba(78, 204, 163, 0.5);
  backdrop-filter: blur(6px);
  border-radius: 1rem;
  color: #fff;
  font-size: 0.8rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  cursor: pointer;
  pointer-events: auto;
}

/* Transitions */
.filter-panel-enter-active,
.filter-panel-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.filter-panel-enter-from,
.filter-panel-leave-to {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.9);
}

.badge-enter-active,
.badge-leave-active {
  transition: opacity 0.3s ease;
}
.badge-enter-from,
.badge-leave-to {
  opacity: 0;
}
</style>
