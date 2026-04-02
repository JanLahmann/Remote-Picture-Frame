<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getStats } from '@/services/api'

const stats = ref<{
  total_photos: number
  visible_photos: number
  hidden_photos: number
  by_channel: Record<string, number>
  by_uploader: Record<string, number>
} | null>(null)

const loading = ref(true)
const error = ref('')

async function loadStats() {
  loading.value = true
  try {
    stats.value = await getStats()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function channelLabel(ch: string): string {
  const labels: Record<string, string> = {
    onedrive: 'OneDrive', email: 'E-Mail',
    whatsapp: 'WhatsApp', web: 'Web-Upload', unknown: 'Unbekannt',
  }
  return labels[ch] || ch
}

const sortedUploaders = computed(() => {
  if (!stats.value) return []
  return Object.entries(stats.value.by_uploader)
    .sort((a, b) => b[1] - a[1])
})

const sortedChannels = computed(() => {
  if (!stats.value) return []
  return Object.entries(stats.value.by_channel)
    .sort((a, b) => b[1] - a[1])
})

onMounted(loadStats)
</script>

<template>
  <div class="dashboard">
    <h2>Uebersicht</h2>

    <div v-if="loading" class="loading">Lade Statistiken...</div>
    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="stats" class="stats-grid">
      <!-- Summary cards -->
      <div class="stat-card accent">
        <div class="stat-value">{{ stats.total_photos }}</div>
        <div class="stat-label">Fotos gesamt</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.visible_photos }}</div>
        <div class="stat-label">Sichtbar</div>
      </div>
      <div class="stat-card" v-if="stats.hidden_photos > 0">
        <div class="stat-value">{{ stats.hidden_photos }}</div>
        <div class="stat-label">Versteckt</div>
      </div>

      <!-- By channel -->
      <div class="stat-section">
        <h3>Nach Upload-Kanal</h3>
        <div class="bar-chart">
          <div v-for="[ch, count] in sortedChannels" :key="ch" class="bar-row">
            <span class="bar-label">{{ channelLabel(ch) }}</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: `${(count / stats.total_photos) * 100}%` }"
              ></div>
            </div>
            <span class="bar-value">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- By uploader -->
      <div class="stat-section">
        <h3>Nach Person</h3>
        <div class="bar-chart">
          <div v-for="[name, count] in sortedUploaders" :key="name" class="bar-row">
            <span class="bar-label">{{ name || 'Unbekannt' }}</span>
            <div class="bar-track">
              <div
                class="bar-fill green"
                :style="{ width: `${(count / stats.total_photos) * 100}%` }"
              ></div>
            </div>
            <span class="bar-value">{{ count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
h2 { margin: 0 0 1rem; font-size: 1.3rem; }
h3 { margin: 0 0 0.6rem; font-size: 1rem; color: #aaa; }
.loading { color: #888; padding: 2rem 0; }
.error { color: #e74c3c; }

.stats-grid { display: flex; flex-direction: column; gap: 1.5rem; }

.stat-card {
  display: inline-flex; flex-direction: column; align-items: center;
  background: #1a1a2e; border: 1px solid #222; border-radius: 12px;
  padding: 1.2rem 2rem; display: inline-block; text-align: center;
  margin-right: 1rem;
}
.stat-card.accent { border-color: #4ecca3; }
.stat-value { font-size: 2.2rem; font-weight: 700; color: #fff; }
.stat-card.accent .stat-value { color: #4ecca3; }
.stat-label { font-size: 0.85rem; color: #888; margin-top: 0.2rem; }

.stat-section {
  background: #1a1a2e; border: 1px solid #222; border-radius: 12px;
  padding: 1rem 1.2rem;
}

.bar-chart { display: flex; flex-direction: column; gap: 0.5rem; }
.bar-row { display: flex; align-items: center; gap: 0.75rem; }
.bar-label { min-width: 100px; font-size: 0.85rem; color: #ccc; text-align: right; }
.bar-track { flex: 1; height: 20px; background: #0f0f1a; border-radius: 4px; overflow: hidden; }
.bar-fill {
  height: 100%; background: #4ecca3; border-radius: 4px;
  min-width: 4px; transition: width 0.5s ease;
}
.bar-fill.green { background: #2ecc71; }
.bar-value { min-width: 35px; font-size: 0.85rem; color: #aaa; font-variant-numeric: tabular-nums; }
</style>
