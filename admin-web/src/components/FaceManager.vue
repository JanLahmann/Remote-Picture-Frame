<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  facesSetup, facesList, facesAddPerson, facesDeletePerson,
  facesAddSample, facesTrain, facesStatus,
} from '@/services/api'

interface Person {
  personId: string
  name: string
  persistedFaceIds: string[]
}

const persons = ref<Person[]>([])
const loading = ref(true)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const newPersonName = ref('')
const trainingStatus = ref('')
const isSetUp = ref(false)

async function load() {
  loading.value = true
  try {
    const result = await facesList()
    persons.value = result.persons || []
    isSetUp.value = true
  } catch {
    isSetUp.value = false
    persons.value = []
  } finally {
    loading.value = false
  }
}

async function setup() {
  try {
    await facesSetup()
    isSetUp.value = true
    showMsg('Gesichtserkennung eingerichtet!', 'success')
    await load()
  } catch (e: any) {
    showMsg('Fehler: ' + e.message, 'error')
  }
}

async function addPerson() {
  const name = newPersonName.value.trim()
  if (!name) return
  try {
    await facesAddPerson(name)
    newPersonName.value = ''
    showMsg(`${name} hinzugefuegt`, 'success')
    await load()
  } catch (e: any) {
    showMsg('Fehler: ' + e.message, 'error')
  }
}

async function removePerson(person: Person) {
  if (!confirm(`${person.name} wirklich entfernen? Alle Beispielbilder gehen verloren.`)) return
  try {
    await facesDeletePerson(person.personId)
    showMsg(`${person.name} entfernt`, 'success')
    await load()
  } catch (e: any) {
    showMsg('Fehler: ' + e.message, 'error')
  }
}

async function addSample(person: Person) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async () => {
    const file = input.files?.[0]
    if (!file) return

    try {
      const b64 = await fileToBase64(file)
      await facesAddSample(person.personId, b64)
      showMsg(`Beispielbild fuer ${person.name} hinzugefuegt (${person.persistedFaceIds.length + 1} gesamt)`, 'success')
      await load()
    } catch (e: any) {
      showMsg('Fehler: ' + e.message, 'error')
    }
  }
  input.click()
}

async function train() {
  try {
    await facesTrain()
    trainingStatus.value = 'Training gestartet...'
    showMsg('Training gestartet. Kann einige Sekunden dauern.', 'success')
    // Poll for status
    setTimeout(checkStatus, 3000)
  } catch (e: any) {
    showMsg('Fehler: ' + e.message, 'error')
  }
}

async function checkStatus() {
  try {
    const result = await facesStatus()
    trainingStatus.value = result.trainingStatus || 'unknown'
    if (trainingStatus.value === 'running') {
      setTimeout(checkStatus, 2000)
    } else if (trainingStatus.value === 'succeeded') {
      showMsg('Training abgeschlossen! Gesichtserkennung ist aktiv.', 'success')
    } else if (trainingStatus.value === 'failed') {
      showMsg('Training fehlgeschlagen: ' + (result.trainingMessage || ''), 'error')
    }
  } catch {
    trainingStatus.value = 'error'
  }
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      resolve(result.split(',')[1])
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function showMsg(msg: string, type: 'success' | 'error') {
  message.value = msg
  messageType.value = type
  setTimeout(() => { message.value = '' }, 6000)
}

onMounted(load)
</script>

<template>
  <div class="face-manager">
    <h2>Gesichtserkennung</h2>
    <p class="subtitle">
      Trainiere die Gesichtserkennung, damit der Bilderrahmen erkennt, wer auf den Fotos zu sehen ist.
      Oma kann dann Fotos nach Personen filtern.
    </p>

    <div v-if="loading" class="loading">Lade...</div>

    <!-- Setup needed -->
    <div v-else-if="!isSetUp" class="setup-prompt">
      <p>Gesichtserkennung ist noch nicht eingerichtet.</p>
      <p class="hint">Voraussetzung: Azure Face API (kostenloser F0-Tarif, 30.000 Anfragen/Monat).</p>
      <button class="action-btn" @click="setup">Gesichtserkennung einrichten</button>
    </div>

    <!-- Person management -->
    <div v-else class="content">
      <!-- Person list -->
      <fieldset>
        <legend>Familienmitglieder</legend>

        <div v-if="persons.length === 0" class="empty">Noch keine Personen angelegt.</div>

        <div v-for="person in persons" :key="person.personId" class="person-card">
          <div class="person-info">
            <span class="person-name">{{ person.name }}</span>
            <span class="face-count">{{ person.persistedFaceIds.length }} Beispielbild{{ person.persistedFaceIds.length !== 1 ? 'er' : '' }}</span>
          </div>
          <div class="person-actions">
            <button class="small-btn" @click="addSample(person)" title="Beispielbild hinzufuegen">+ Foto</button>
            <button class="small-btn danger" @click="removePerson(person)" title="Person entfernen">&times;</button>
          </div>
        </div>

        <!-- Add person -->
        <div class="add-row">
          <input
            type="text"
            v-model="newPersonName"
            placeholder="Name eingeben..."
            @keydown.enter.prevent="addPerson"
          />
          <button class="add-btn" @click="addPerson">Hinzufuegen</button>
        </div>
      </fieldset>

      <!-- Training -->
      <fieldset>
        <legend>Training</legend>
        <p class="hint">
          Nach dem Hinzufuegen oder Aendern von Beispielbildern muss das Modell neu trainiert werden.
          Jede Person braucht mindestens 1 Beispielbild (3-6 sind ideal).
        </p>

        <div class="train-row">
          <button class="action-btn" @click="train">Modell trainieren</button>
          <span v-if="trainingStatus" :class="['train-status', trainingStatus]">
            {{ trainingStatus === 'succeeded' ? 'Aktiv' : trainingStatus === 'running' ? 'Laeuft...' : trainingStatus === 'failed' ? 'Fehlgeschlagen' : trainingStatus }}
          </span>
        </div>
      </fieldset>

      <!-- Status message -->
      <p v-if="message" :class="['message', messageType]">{{ message }}</p>
    </div>
  </div>
</template>

<style scoped>
h2 { margin: 0 0 0.3rem; font-size: 1.3rem; }
.subtitle { color: #888; font-size: 0.85rem; margin: 0 0 1.5rem; line-height: 1.4; }
.loading { color: #888; padding: 2rem 0; }
.hint { color: #888; font-size: 0.8rem; line-height: 1.4; margin: 0; }
.empty { color: #666; font-style: italic; font-size: 0.9rem; }

.content { display: flex; flex-direction: column; gap: 1.2rem; }

.setup-prompt {
  text-align: center; padding: 2rem 0;
  display: flex; flex-direction: column; gap: 1rem; align-items: center;
}

fieldset {
  border: 1px solid #222; border-radius: 12px; padding: 1rem 1.2rem;
  margin: 0; display: flex; flex-direction: column; gap: 0.8rem;
}
legend { color: #4ecca3; font-weight: 600; font-size: 0.9rem; padding: 0 0.5rem; }

.person-card {
  display: flex; justify-content: space-between; align-items: center;
  background: #0f0f1a; border: 1px solid #333; border-radius: 8px;
  padding: 0.6rem 0.8rem;
}

.person-info { display: flex; flex-direction: column; gap: 0.15rem; }
.person-name { font-weight: 600; font-size: 0.95rem; }
.face-count { font-size: 0.75rem; color: #888; }

.person-actions { display: flex; gap: 0.4rem; }

.small-btn {
  padding: 0.35rem 0.6rem; background: #242442; border: 1px solid #444;
  border-radius: 6px; color: #e0e0e0; font-size: 0.8rem; cursor: pointer;
}
.small-btn:hover { border-color: #4ecca3; }
.small-btn.danger:hover { border-color: #e74c3c; color: #e74c3c; }

.add-row {
  display: flex; gap: 0.5rem;
}
.add-row input {
  flex: 1; padding: 0.5rem 0.75rem; background: #0f0f1a; border: 1px solid #333;
  border-radius: 8px; color: #e0e0e0; font-size: 0.9rem;
}
.add-row input:focus { outline: none; border-color: #4ecca3; }

.add-btn {
  padding: 0.5rem 1rem; background: #4ecca3; color: #000; border: none;
  border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
  white-space: nowrap;
}
.add-btn:hover { background: #3db88f; }

.action-btn {
  padding: 0.6rem 1.2rem; background: #4ecca3; color: #000; border: none;
  border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer;
}
.action-btn:hover { background: #3db88f; }

.train-row { display: flex; align-items: center; gap: 1rem; }
.train-status { font-size: 0.85rem; font-weight: 600; }
.train-status.succeeded { color: #4ecca3; }
.train-status.running { color: #f0c040; }
.train-status.failed { color: #e74c3c; }

.message {
  padding: 0.6rem 1rem; border-radius: 8px; font-size: 0.9rem; margin: 0;
}
.message.success { background: rgba(78,204,163,0.15); color: #4ecca3; }
.message.error { background: rgba(231,76,60,0.15); color: #e74c3c; }
</style>
