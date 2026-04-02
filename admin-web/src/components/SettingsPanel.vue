<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSettings, updateSettings } from '@/services/api'

const loading = ref(true)
const saving = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const settings = ref({
  slideshow_interval: 30,
  transition: 'fade' as 'fade' | 'slide' | 'kenburns',
  transition_duration: 1.5,
  order: 'random' as 'random' | 'newest' | 'chronological',
  show_overlay: true,
  overlay_duration: 5,
  night_mode: {
    enabled: true,
    dim_start: '22:00',
    dim_end: '07:00',
    brightness: 0.1,
  },
  sync_interval: 5,
  family_members: [] as string[],
})

const newMemberName = ref('')

function addMember() {
  const name = newMemberName.value.trim()
  if (!name) return
  if (settings.value.family_members.includes(name)) {
    newMemberName.value = ''
    return
  }
  settings.value.family_members.push(name)
  settings.value.family_members.sort()
  newMemberName.value = ''
}

function removeMember(index: number) {
  settings.value.family_members.splice(index, 1)
}

async function loadSettings() {
  loading.value = true
  try {
    const result = await getSettings()
    settings.value = { ...settings.value, ...result }
  } catch (e: any) {
    showMessage('Einstellungen konnten nicht geladen werden: ' + e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  message.value = ''
  try {
    await updateSettings(settings.value)
    showMessage('Einstellungen gespeichert! Der Bilderrahmen uebernimmt sie in ~10 Minuten.', 'success')
  } catch (e: any) {
    showMessage('Fehler: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

function showMessage(msg: string, type: 'success' | 'error') {
  message.value = msg
  messageType.value = type
  setTimeout(() => { message.value = '' }, 6000)
}

onMounted(loadSettings)
</script>

<template>
  <div class="settings-panel">
    <h2>Einstellungen</h2>
    <p class="subtitle">Aenderungen werden in OneDrive gespeichert und vom Bilderrahmen automatisch uebernommen.</p>

    <div v-if="loading" class="loading">Lade Einstellungen...</div>

    <form v-else @submit.prevent="saveSettings" class="form">
      <!-- Slideshow -->
      <fieldset>
        <legend>Slideshow</legend>

        <div class="field">
          <label>Anzeigedauer pro Foto</label>
          <div class="range-group">
            <input type="range" v-model.number="settings.slideshow_interval" min="5" max="300" step="5" />
            <span class="range-value">{{ settings.slideshow_interval }}s</span>
          </div>
        </div>

        <div class="field">
          <label>Uebergang</label>
          <select v-model="settings.transition">
            <option value="fade">Ueberblenden (Fade)</option>
            <option value="slide">Schieben (Slide)</option>
            <option value="kenburns">Ken Burns (Zoom)</option>
          </select>
        </div>

        <div class="field">
          <label>Uebergangsdauer</label>
          <div class="range-group">
            <input type="range" v-model.number="settings.transition_duration" min="0.3" max="3" step="0.1" />
            <span class="range-value">{{ settings.transition_duration.toFixed(1) }}s</span>
          </div>
        </div>

        <div class="field">
          <label>Reihenfolge</label>
          <select v-model="settings.order">
            <option value="random">Zufaellig</option>
            <option value="newest">Neueste zuerst</option>
            <option value="chronological">Chronologisch</option>
          </select>
        </div>
      </fieldset>

      <!-- Overlay -->
      <fieldset>
        <legend>Bildunterschrift</legend>

        <div class="field checkbox">
          <input type="checkbox" id="showOverlay" v-model="settings.show_overlay" />
          <label for="showOverlay">Bildunterschrift anzeigen</label>
        </div>

        <div class="field" v-if="settings.show_overlay">
          <label>Einblenddauer (0 = immer sichtbar)</label>
          <div class="range-group">
            <input type="range" v-model.number="settings.overlay_duration" min="0" max="30" step="1" />
            <span class="range-value">{{ settings.overlay_duration === 0 ? 'Immer' : settings.overlay_duration + 's' }}</span>
          </div>
        </div>
      </fieldset>

      <!-- Night mode -->
      <fieldset>
        <legend>Nachtmodus</legend>

        <div class="field checkbox">
          <input type="checkbox" id="nightEnabled" v-model="settings.night_mode.enabled" />
          <label for="nightEnabled">Nachtmodus aktivieren</label>
        </div>

        <template v-if="settings.night_mode.enabled">
          <div class="field-row">
            <div class="field">
              <label>Abdunkeln ab</label>
              <input type="time" v-model="settings.night_mode.dim_start" />
            </div>
            <div class="field">
              <label>Aufhellen ab</label>
              <input type="time" v-model="settings.night_mode.dim_end" />
            </div>
          </div>

          <div class="field">
            <label>Helligkeit im Nachtmodus</label>
            <div class="range-group">
              <input type="range" v-model.number="settings.night_mode.brightness" min="0" max="0.5" step="0.05" />
              <span class="range-value">{{ Math.round(settings.night_mode.brightness * 100) }}%</span>
            </div>
          </div>
        </template>
      </fieldset>

      <!-- Family Members -->
      <fieldset>
        <legend>Familienmitglieder</legend>
        <p class="field-hint">Diese Namen erscheinen im Dropdown der Upload-Seite und im Personenfilter auf dem Bilderrahmen.</p>

        <div class="member-list">
          <div v-for="(name, i) in settings.family_members" :key="name" class="member-item">
            <span>{{ name }}</span>
            <button type="button" class="remove-btn" @click="removeMember(i)" title="Entfernen">&times;</button>
          </div>
          <div v-if="settings.family_members.length === 0" class="empty-hint">
            Noch keine Mitglieder hinzugefuegt.
          </div>
        </div>

        <div class="add-member">
          <input
            type="text"
            v-model="newMemberName"
            placeholder="Name eingeben..."
            @keydown.enter.prevent="addMember"
          />
          <button type="button" class="add-btn" @click="addMember">Hinzufuegen</button>
        </div>
      </fieldset>

      <!-- Sync -->
      <fieldset>
        <legend>Synchronisation</legend>
        <div class="field">
          <label>Sync-Intervall</label>
          <div class="range-group">
            <input type="range" v-model.number="settings.sync_interval" min="1" max="30" step="1" />
            <span class="range-value">{{ settings.sync_interval }} Min.</span>
          </div>
        </div>
      </fieldset>

      <!-- Status message -->
      <p v-if="message" :class="['message', messageType]">{{ message }}</p>

      <!-- Save -->
      <button type="submit" class="save-btn" :disabled="saving">
        {{ saving ? 'Speichere...' : 'Einstellungen speichern' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
h2 { margin: 0 0 0.3rem; font-size: 1.3rem; }
.subtitle { color: #888; font-size: 0.85rem; margin: 0 0 1.5rem; }
.loading { color: #888; padding: 2rem 0; }

.form { display: flex; flex-direction: column; gap: 1.2rem; }

fieldset {
  border: 1px solid #222; border-radius: 12px; padding: 1rem 1.2rem;
  margin: 0; display: flex; flex-direction: column; gap: 0.8rem;
}
legend { color: #4ecca3; font-weight: 600; font-size: 0.9rem; padding: 0 0.5rem; }

.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field label { font-size: 0.85rem; color: #aaa; }
.field.checkbox { flex-direction: row; align-items: center; gap: 0.5rem; }
.field.checkbox label { cursor: pointer; }
.field.checkbox input { width: 18px; height: 18px; accent-color: #4ecca3; }

.field-row { display: flex; gap: 1rem; }
.field-row .field { flex: 1; }

select, input[type="time"] {
  padding: 0.6rem; background: #0f0f1a; border: 1px solid #333;
  border-radius: 8px; color: #e0e0e0; font-size: 0.95rem;
}
select:focus, input[type="time"]:focus { outline: none; border-color: #4ecca3; }

.range-group { display: flex; align-items: center; gap: 0.75rem; }
.range-group input[type="range"] { flex: 1; accent-color: #4ecca3; }
.range-value {
  min-width: 55px; text-align: right; font-size: 0.9rem;
  color: #e0e0e0; font-variant-numeric: tabular-nums;
}

.message {
  padding: 0.6rem 1rem; border-radius: 8px; font-size: 0.9rem; margin: 0;
}
.message.success { background: rgba(78,204,163,0.15); color: #4ecca3; }
.message.error { background: rgba(231,76,60,0.15); color: #e74c3c; }

.field-hint {
  font-size: 0.8rem; color: #888; margin: 0 0 0.3rem; line-height: 1.4;
}

.member-list {
  display: flex; flex-wrap: wrap; gap: 0.4rem;
}

.member-item {
  display: flex; align-items: center; gap: 0.3rem;
  background: #0f0f1a; border: 1px solid #333; border-radius: 2rem;
  padding: 0.35rem 0.5rem 0.35rem 0.75rem; font-size: 0.9rem;
}

.remove-btn {
  background: none; border: none; color: #e74c3c; font-size: 1.1rem;
  cursor: pointer; line-height: 1; padding: 0 0.2rem;
}
.remove-btn:hover { color: #ff6b6b; }

.empty-hint { font-size: 0.85rem; color: #666; font-style: italic; }

.add-member {
  display: flex; gap: 0.5rem;
}

.add-member input {
  flex: 1; padding: 0.5rem 0.75rem; background: #0f0f1a; border: 1px solid #333;
  border-radius: 8px; color: #e0e0e0; font-size: 0.9rem;
}
.add-member input:focus { outline: none; border-color: #4ecca3; }

.add-btn {
  padding: 0.5rem 1rem; background: #4ecca3; color: #000; border: none;
  border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
  white-space: nowrap;
}
.add-btn:hover { background: #3db88f; }

.save-btn {
  padding: 0.8rem; background: #4ecca3; color: #000; border: none;
  border-radius: 10px; font-size: 1rem; font-weight: 700; cursor: pointer;
}
.save-btn:hover { background: #3db88f; }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
