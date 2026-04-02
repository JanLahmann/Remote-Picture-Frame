<script setup lang="ts">
import { ref } from 'vue'
import Dashboard from '@/components/Dashboard.vue'
import PhotoGrid from '@/components/PhotoGrid.vue'
import SettingsPanel from '@/components/SettingsPanel.vue'
import FaceManager from '@/components/FaceManager.vue'

type Tab = 'dashboard' | 'photos' | 'settings' | 'faces'
const activeTab = ref<Tab>('dashboard')

const tabs: { id: Tab; label: string }[] = [
  { id: 'dashboard', label: 'Uebersicht' },
  { id: 'photos', label: 'Fotos' },
  { id: 'faces', label: 'Gesichter' },
  { id: 'settings', label: 'Einstellungen' },
]
</script>

<template>
  <div class="admin-app">
    <header>
      <div class="header-inner">
        <h1>FamilyFrame <span class="admin-badge">Admin</span></h1>
        <nav>
          <button
            v-for="tab in tabs" :key="tab.id"
            :class="['tab', { active: activeTab === tab.id }]"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>
    </header>

    <main>
      <Dashboard v-if="activeTab === 'dashboard'" />
      <PhotoGrid v-if="activeTab === 'photos'" />
      <FaceManager v-if="activeTab === 'faces'" />
      <SettingsPanel v-if="activeTab === 'settings'" />
    </main>
  </div>
</template>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f0f1a;
  color: #e0e0e0;
  min-height: 100vh;
}

.admin-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

header {
  background: #1a1a2e;
  border-bottom: 1px solid #222;
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}

h1 {
  font-size: 1.2rem;
  font-weight: 700;
  color: #4ecca3;
}

.admin-badge {
  font-size: 0.7rem;
  background: #4ecca3;
  color: #000;
  padding: 2px 6px;
  border-radius: 4px;
  vertical-align: middle;
  margin-left: 0.3rem;
  font-weight: 700;
  text-transform: uppercase;
}

nav {
  display: flex;
  gap: 0.25rem;
}

.tab {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #888;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.tab:hover { background: #242442; color: #ccc; }
.tab.active { background: #242442; color: #fff; font-weight: 600; }

main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
  width: 100%;
  flex: 1;
}
</style>
