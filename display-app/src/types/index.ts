export interface PhotoLocation {
  lat: number
  lon: number
  name?: string
}

export interface Photo {
  id: string
  filename: string
  caption: string
  description: string
  date_taken: string | null
  location: PhotoLocation | null
  uploaded_by: string
  uploaded_at: string
  download_url: string | null
  thumbnail_url: string
  tags: string[]
  people: string[]
}

export interface SyncResponse {
  photos: Photo[]
  count: number
  synced_at: string
}

export interface NightModeSettings {
  enabled: boolean
  dim_start: string  // "HH:MM"
  dim_end: string    // "HH:MM"
  brightness: number // 0.0 - 1.0
}

export interface DisplaySettings {
  slideshow_interval: number    // seconds between photos
  transition: 'fade' | 'slide' | 'kenburns'
  transition_duration: number   // seconds
  order: 'random' | 'newest' | 'chronological'
  show_overlay: boolean
  overlay_duration: number      // seconds (0 = always visible)
  night_mode: NightModeSettings
  sync_interval: number         // minutes
}

export const DEFAULT_SETTINGS: DisplaySettings = {
  slideshow_interval: 30,
  transition: 'fade',
  transition_duration: 1.5,
  order: 'random',
  show_overlay: true,
  overlay_duration: 5,
  night_mode: {
    enabled: true,
    dim_start: '22:00',
    dim_end: '07:00',
    brightness: 0.1,
  },
  sync_interval: 5,
}
