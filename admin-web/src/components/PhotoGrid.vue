<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { listPhotos, toggleVisibility, deletePhoto, updatePhoto, getSettings } from '@/services/api'

interface Photo {
  id: string
  filename: string
  caption: string
  description: string
  date_taken: string | null
  location: { lat: number; lon: number; name?: string } | null
  uploaded_by: string
  uploaded_at: string
  upload_channel: string
  visible: boolean
  tags: string[]
  people: string[]
  favorite: boolean
  album: string
  thumbnail_url: string
}

interface Album {
  id: string
  name: string
  description: string
}

const photos = ref<Photo[]>([])
const loading = ref(true)
const error = ref('')
const editingPhoto = ref<Photo | null>(null)
const editCaption = ref('')
const editDescription = ref('')
const editAlbum = ref('')
const filterChannel = ref('all')
const albums = ref<Album[]>([])

async function loadPhotos() {
  loading.value = true
  error.value = ''
  try {
    const result = await listPhotos(200)
    photos.value = result.photos
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const filteredPhotos = computed(() => {
  if (filterChannel.value === 'all') return photos.value
  return photos.value.filter(p => p.upload_channel === filterChannel.value)
})

const channels = computed(() => {
  const set = new Set(photos.value.map(p => p.upload_channel))
  return ['all', ...Array.from(set)]
})

async function onToggleVisibility(photo: Photo) {
  try {
    const result = await toggleVisibility(photo.id)
    photo.visible = result.visible
  } catch (e: any) {
    error.value = e.message
  }
}

async function onDelete(photo: Photo) {
  if (!confirm(`"${photo.filename}" wirklich loeschen?`)) return
  try {
    await deletePhoto(photo.id)
    photos.value = photos.value.filter(p => p.id !== photo.id)
  } catch (e: any) {
    error.value = e.message
  }
}

function startEdit(photo: Photo) {
  editingPhoto.value = photo
  editCaption.value = photo.caption
  editDescription.value = photo.description
  editAlbum.value = photo.album || ''
}

function cancelEdit() {
  editingPhoto.value = null
}

async function saveEdit() {
  if (!editingPhoto.value) return
  try {
    await updatePhoto(editingPhoto.value.id, {
      caption: editCaption.value,
      description: editDescription.value,
      album: editAlbum.value,
    })
    editingPhoto.value.caption = editCaption.value
    editingPhoto.value.description = editDescription.value
    editingPhoto.value.album = editAlbum.value
    editingPhoto.value = null
  } catch (e: any) {
    error.value = e.message
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleDateString('de-DE', {
      day: 'numeric', month: 'short', year: 'numeric',
    })
  } catch { return '' }
}

function channelLabel(ch: string): string {
  const labels: Record<string, string> = {
    all: 'Alle', onedrive: 'OneDrive', email: 'E-Mail',
    whatsapp: 'WhatsApp', web: 'Web-Upload',
  }
  return labels[ch] || ch
}

async function loadAlbums() {
  try {
    const result = await getSettings()
    albums.value = result.albums || []
  } catch { /* ignore */ }
}

onMounted(() => {
  loadPhotos()
  loadAlbums()
})
</script>

<template>
  <div class="photo-grid-section">
    <!-- Toolbar -->
    <div class="toolbar">
      <h2>Fotos ({{ filteredPhotos.length }})</h2>
      <div class="filters">
        <button
          v-for="ch in channels" :key="ch"
          :class="['filter-btn', { active: filterChannel === ch }]"
          @click="filterChannel = ch"
        >
          {{ channelLabel(ch) }}
        </button>
      </div>
      <button class="refresh-btn" @click="loadPhotos" :disabled="loading">
        {{ loading ? 'Lade...' : 'Aktualisieren' }}
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <!-- Photo grid -->
    <div class="grid">
      <div
        v-for="photo in filteredPhotos" :key="photo.id"
        class="card"
        :class="{ hidden: !photo.visible }"
      >
        <div class="card-image">
          <img
            v-if="photo.thumbnail_url"
            :src="photo.thumbnail_url"
            :alt="photo.filename"
            loading="lazy"
          />
          <div v-else class="placeholder">Kein Bild</div>
          <span v-if="!photo.visible" class="hidden-badge">Versteckt</span>
          <span v-if="photo.favorite" class="fav-badge">&hearts;</span>
          <span class="channel-badge">{{ channelLabel(photo.upload_channel) }}</span>
        </div>

        <div class="card-body">
          <p class="caption">{{ photo.caption || photo.filename }}</p>
          <p v-if="photo.description" class="desc">{{ photo.description }}</p>
          <div class="meta">
            <span v-if="photo.uploaded_by">{{ photo.uploaded_by }}</span>
            <span v-if="photo.date_taken">{{ formatDate(photo.date_taken) }}</span>
            <span v-if="photo.location?.name">{{ photo.location.name }}</span>
          </div>
          <div class="meta" v-if="photo.people?.length || photo.album">
            <span v-if="photo.people?.length" class="tag">{{ photo.people.join(', ') }}</span>
            <span v-if="photo.album" class="tag album-tag">{{ albums.find(a => a.id === photo.album)?.name || photo.album }}</span>
          </div>
        </div>

        <div class="card-actions">
          <button @click="startEdit(photo)" title="Bearbeiten">Bearbeiten</button>
          <button @click="onToggleVisibility(photo)" :title="photo.visible ? 'Verstecken' : 'Anzeigen'">
            {{ photo.visible ? 'Verstecken' : 'Anzeigen' }}
          </button>
          <button class="danger" @click="onDelete(photo)" title="Loeschen">Loeschen</button>
        </div>
      </div>
    </div>

    <!-- Edit modal -->
    <div v-if="editingPhoto" class="modal-overlay" @click.self="cancelEdit">
      <div class="modal">
        <h3>Foto bearbeiten</h3>
        <div class="form-field">
          <label>Bildunterschrift</label>
          <input v-model="editCaption" type="text" />
        </div>
        <div class="form-field">
          <label>Beschreibung</label>
          <textarea v-model="editDescription" rows="3"></textarea>
        </div>
        <div class="form-field" v-if="albums.length > 0">
          <label>Album</label>
          <select v-model="editAlbum">
            <option value="">Kein Album</option>
            <option v-for="a in albums" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button @click="cancelEdit">Abbrechen</button>
          <button class="primary" @click="saveEdit">Speichern</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.toolbar h2 { margin: 0; font-size: 1.3rem; }
.filters { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.filter-btn {
  padding: 0.35rem 0.75rem; border: 1px solid #333; border-radius: 20px;
  background: transparent; color: #aaa; cursor: pointer; font-size: 0.85rem;
}
.filter-btn.active { background: #4ecca3; color: #000; border-color: #4ecca3; }
.refresh-btn {
  margin-left: auto; padding: 0.4rem 1rem; background: #1a1a2e;
  border: 1px solid #333; border-radius: 8px; color: #aaa; cursor: pointer;
}
.refresh-btn:disabled { opacity: 0.5; }
.error { color: #e74c3c; background: rgba(231,76,60,0.1); padding: 0.5rem 1rem; border-radius: 8px; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
}
.card {
  background: #1a1a2e; border-radius: 12px; overflow: hidden;
  border: 1px solid #222; transition: border-color 0.2s;
}
.card:hover { border-color: #4ecca3; }
.card.hidden { opacity: 0.55; }
.card-image { position: relative; aspect-ratio: 4/3; background: #111; }
.card-image img { width: 100%; height: 100%; object-fit: cover; }
.placeholder {
  width: 100%; height: 100%; display: flex; align-items: center;
  justify-content: center; color: #555;
}
.hidden-badge {
  position: absolute; top: 8px; left: 8px; background: rgba(231,76,60,0.9);
  color: #fff; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px;
}
.fav-badge {
  position: absolute; top: 8px; left: 8px; color: #e74c64; font-size: 1rem;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5);
}
.channel-badge {
  position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.7);
  color: #ccc; font-size: 0.7rem; padding: 2px 8px; border-radius: 4px;
}
.tag {
  font-size: 0.7rem; background: #242442; padding: 1px 6px; border-radius: 4px; color: #aaa;
}
.album-tag { background: rgba(160,120,240,0.2); color: #b09ae0; }
.card-body { padding: 0.75rem; }
.caption { font-weight: 600; font-size: 0.95rem; margin: 0 0 0.25rem; }
.desc { font-size: 0.85rem; color: #aaa; margin: 0 0 0.4rem; }
.meta { display: flex; gap: 0.75rem; font-size: 0.78rem; color: #666; flex-wrap: wrap; }
.card-actions {
  display: flex; gap: 0.5rem; padding: 0 0.75rem 0.75rem;
}
.card-actions button {
  flex: 1; padding: 0.4rem; font-size: 0.8rem; border-radius: 6px;
  border: 1px solid #333; background: transparent; color: #aaa; cursor: pointer;
}
.card-actions button:hover { background: #242442; color: #fff; }
.card-actions button.danger:hover { background: rgba(231,76,60,0.2); color: #e74c3c; border-color: #e74c3c; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex;
  align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: #1a1a2e; border-radius: 12px; padding: 1.5rem; width: 90%;
  max-width: 450px; border: 1px solid #333;
}
.modal h3 { margin: 0 0 1rem; }
.form-field { margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.3rem; }
.form-field label { font-size: 0.85rem; color: #888; }
.form-field input, .form-field textarea {
  padding: 0.6rem; background: #0f0f1a; border: 1px solid #333;
  border-radius: 8px; color: #e0e0e0; font-size: 0.95rem; font-family: inherit;
}
.form-field input:focus, .form-field textarea:focus { outline: none; border-color: #4ecca3; }
.modal-actions { display: flex; gap: 0.75rem; justify-content: flex-end; }
.modal-actions button {
  padding: 0.5rem 1.2rem; border-radius: 8px; border: 1px solid #333;
  background: transparent; color: #aaa; cursor: pointer;
}
.modal-actions button.primary { background: #4ecca3; color: #000; border-color: #4ecca3; font-weight: 600; }
</style>
