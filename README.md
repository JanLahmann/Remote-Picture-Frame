# FamilyFrame - Digitaler Bilderrahmen fuer die Familie

Ein digitaler Bilderrahmen, der Fotos der ganzen Familie anzeigt. Familienmitglieder laden Fotos vom Handy hoch — per OneDrive-App, E-Mail oder WhatsApp. Omas Display zeigt sie automatisch an. Keine Interaktion noetig.

## Wie es funktioniert

```
Familie                         Cloud                          Omas Display
────────                       ───────                        ─────────────

OneDrive App ──────────────→                                  ┌────────────┐
                               OneDrive ← IBM Cloud ──sync──→│ Slideshow  │
E-Mail ──→ Power Automate ──→  Shared     Functions           │ + Captions │
                               Folder                         │ + Datum    │
WhatsApp ──→ Twilio ────────→                                 │ + Ort      │
                               Cloudant                       └────────────┘
                               (Metadaten)                    Android / iPad
                                                              / Raspberry Pi
```

**Familienmitglieder** (bis zu 20+) laden Fotos ueber drei Wege hoch:
- **OneDrive App** — Fotos direkt in den geteilten Ordner laden
- **E-Mail** — Foto als Anhang an eine dedizierte Adresse schicken (Betreff = Bildunterschrift)
- **WhatsApp** — Foto an eine WhatsApp-Nummer senden (Nachricht = Bildunterschrift)

**Omas Bilderrahmen** zeigt die Fotos als Slideshow — vollautomatisch, ohne jede Interaktion. Optional: Touch-Steuerung (tippen, wischen, pausieren).

## Features

- **Slideshow** mit konfigurierbaren Uebergaengen (Fade, Slide, Ken Burns)
- **Bildunterschriften**: Caption, Beschreibung, Datum, Ort, Absender
- **Touch-Steuerung**: Tippen (vor/zurueck), Wischen (Overlay ein/aus), Doppeltippen (Pause)
- **Nachtmodus**: Automatische Abdunkelung nach Zeitplan
- **Offline-Faehig**: Service Worker cached Fotos lokal — funktioniert auch bei WLAN-Ausfall
- **Fernkonfiguration**: Slideshow-Einstellungen per `settings.json` in OneDrive aendern
- **Fernwartung**: Fully Kiosk Browser (Android) + TeamViewer fuer Remote-Zugriff
- **Multi-Plattform**: Laeuft auf Android-Tablets, iPads und Raspberry Pi (als PWA)
- **EXIF-Extraktion**: Datum, GPS-Koordinaten und Kamera werden automatisch aus Fotos gelesen
- **Komplett kostenlos**: 0 EUR/Monat (alle Dienste auf Free Tiers, inkl. WhatsApp)

## Tech Stack

| Komponente | Technologie |
|-----------|-------------|
| Foto-Speicher | OneDrive (Microsoft 365) |
| Backend | IBM Cloud Functions (Python, serverless) |
| Metadaten-DB | IBM Cloudant (CouchDB, Lite Plan) |
| E-Mail-Eingang | Power Automate (in M365 enthalten) |
| WhatsApp | Meta WhatsApp Cloud API (free tier) |
| Display-App | Progressive Web App (Vue.js 3, TypeScript, Vite) |
| PWA-Hosting | IBM Cloud Object Storage |

## Projektstruktur

```
backend/                    IBM Cloud Functions (Python)
  shared/                   Geteilte Module (OneDrive, Cloudant, EXIF)
  packages/                 Cloud Functions (process_new_photo, display_sync_api, ...)
  deploy.sh                 Deployment-Skript

display-app/                PWA Display-App (Vue.js 3 + TypeScript)
  src/components/           Slideshow, PhotoOverlay, TouchControls
  src/composables/          useSync, useSlideshow, useSettings
  src/services/             API-Client, Cache-Management
  public/sw.js              Service Worker fuer Offline-Support

raspberry-pi/               Raspberry Pi Kiosk-Modus Setup
  setup.sh                  Automatisiertes Setup-Skript

docs/                       Dokumentation
  setup-ibmcloud.md         IBM Cloud + Graph API Einrichtung
  setup-onedrive.md         OneDrive Ordner + Freigabe
  setup-display.md          Tablet / iPad / Raspberry Pi Einrichtung
  setup-email-powerautomate.md  E-Mail-Upload mit Power Automate
  family-guide-de.md        Anleitung fuer die Familie (Deutsch)
```

## Schnellstart

### Voraussetzungen

- Microsoft 365 Konto (fuer OneDrive + Power Automate)
- IBM Cloud Konto (kostenlos)
- Node.js 18+ und Python 3.11+

### 1. Backend deployen

```bash
# Konfiguration erstellen (siehe docs/setup-ibmcloud.md)
cp backend/local.settings.example.json backend/local.settings.json
# ... Werte eintragen ...

# Deployen
cd backend
./deploy.sh
```

### 2. PWA bauen und deployen

```bash
cd display-app
npm install
echo 'VITE_API_BASE=https://...' > .env.production
echo 'VITE_DEVICE_TOKEN=...' >> .env.production
npm run build
# dist/ Ordner auf IBM Cloud Object Storage hochladen
```

### 3. Display einrichten

**Android-Tablet**: Fully Kiosk Browser installieren, PWA-URL eintragen. Details: [docs/setup-display.md](docs/setup-display.md)

**Raspberry Pi**: `sudo ./raspberry-pi/setup.sh https://deine-url.example.com`

### 4. OneDrive teilen

Ordner `/FamilyFrame/photos/` mit der Familie teilen. Details: [docs/setup-onedrive.md](docs/setup-onedrive.md)

## Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| [PLAN.md](PLAN.md) | Vollstaendiger Projektplan (Architektur, Phasen, Entscheidungen) |
| [docs/setup-ibmcloud.md](docs/setup-ibmcloud.md) | IBM Cloud + Microsoft Graph API Einrichtung |
| [docs/setup-onedrive.md](docs/setup-onedrive.md) | OneDrive Ordnerstruktur + Familie einladen |
| [docs/setup-display.md](docs/setup-display.md) | Display-Geraet einrichten (Android / iPad / RPi) |
| [docs/setup-email-powerautomate.md](docs/setup-email-powerautomate.md) | E-Mail-Upload mit Power Automate |
| [docs/family-guide-de.md](docs/family-guide-de.md) | Einfache Anleitung fuer Familienmitglieder |

## Hardware-Empfehlung

| Option | Geraet | Preis |
|--------|--------|-------|
| **Empfohlen** | Samsung Galaxy Tab A9+ (11", WiFi) + Staender | ~270 EUR |
| Budget | Raspberry Pi 4 + 10" Display + Gehaeuse | ~160 EUR |
| Vorhanden | Beliebiges iPad (iOS 15+) | 0 EUR |

## Lizenz

[MIT](LICENSE)
