# Remote Picture Frame - Project Plan

## Vision

A digital picture frame for grandma. Family members (~20 people) upload photos from their phones via multiple channels. Grandma's display shows them automatically — zero interaction required, but touch controls available. Ease of use is the top priority.

---

## 1. Architecture Overview

```
Upload Channels              Processing               Storage            Display
───────────────             ────────────             ─────────          ─────────

OneDrive App ─────────────────────────────────────→ OneDrive  ←──sync──→ Android
(direct upload)                                     Shared       (Graph   Tablet
                                                    Folder       API)     (Kiosk
Email ──→ Power Automate ──→ Save to OneDrive ───→ /Family               Mode)
          (M365 included)    + extract caption       Frame/
                                                                  ┌──────────────┐
WhatsApp ──→ Twilio ──→ Azure Function ──→ OneDrive              │  Slideshow    │
(Phase 2)    Webhook     (process + save)                        │  + Captions   │
                                                                  │  + Date/Loc   │
                                               Metadata DB        │  + Touch Nav  │
                                               (Cosmos DB         └──────────────┘
                                                free tier)
```

### Core Principle: OneDrive as Single Source of Truth

The family already has OneDrive (1TB, M365). Every upload channel funnels photos into one shared OneDrive folder. The tablet syncs from there. This keeps things simple and familiar.

---

## 2. Components

### 2.1 OneDrive Shared Folder Structure

```
/FamilyFrame/
  /photos/                  ← all photos land here
  /config/
    settings.json           ← slideshow settings, synced to tablet
```

### 2.2 Metadata Storage (Azure Cosmos DB - Free Tier)

Each photo gets a metadata record:

```json
{
  "id": "abc123",
  "onedrive_item_id": "ABCDEF...",
  "filename": "beach_2026.jpg",
  "caption": "Urlaub an der Ostsee",
  "description": "Die Kinder bauen eine Sandburg",
  "date_taken": "2026-07-15T14:30:00Z",
  "location": { "lat": 54.18, "lon": 12.08, "name": "Warnemuende" },
  "uploaded_by": "Maria",
  "upload_channel": "email",
  "uploaded_at": "2026-07-15T18:00:00Z",
  "visible": true,
  "tags": []
}
```

**Why a separate DB and not just OneDrive file properties?**
- OneDrive file descriptions are limited and not easily queryable
- Cosmos DB free tier gives us 1000 RU/s and 25 GB — more than enough
- Enables filtering, search, and admin features later
- Consistent metadata regardless of upload channel

### 2.3 Upload Channel: OneDrive App (Built-in)

- Family members install OneDrive on their phones (most will already have it)
- They upload photos to the shared `/FamilyFrame/photos/` folder
- An **Azure Function** monitors the folder via Microsoft Graph API webhooks (change notifications)
- On new photo: extract EXIF data (date, GPS), create metadata record in Cosmos DB
- Family members can optionally add a description in OneDrive's file properties → gets pulled into metadata

### 2.4 Upload Channel: Email

- Dedicated email address: e.g. `bilderrahmen@family-domain.de` (or a shared mailbox in M365)
- **Power Automate flow** (included in M365, no extra cost):
  1. Trigger: new email arrives at the shared mailbox
  2. For each attachment (filter: image files only):
     - Save to `/FamilyFrame/photos/`
     - Subject line → caption
     - Email body → description
     - Sender → uploaded_by
  3. The same Azure Function picks up the new file and creates the metadata record
- **Bonus**: Works from any device, any platform — just send an email with photos attached

### 2.5 Upload Channel: WhatsApp (Phase 2)

- Dedicated WhatsApp number via **Twilio WhatsApp Business API**
- Family members send photos (and optional caption as message text) to this number
- Twilio webhook → **Azure Function**:
  1. Download the media from Twilio
  2. Upload to OneDrive `/FamilyFrame/photos/`
  3. Extract caption from message text
  4. Create metadata record
- **Cost**: Twilio WhatsApp is ~€0.005/message received + phone number ~€1/month
- **Alternative** (lower cost, more fragile): WhatsApp Web automation via a headless browser on a small VM. Not recommended for reliability.

### 2.6 Backend: Azure Functions (Serverless)

All backend logic runs as Azure Functions (Python):

| Function | Trigger | Purpose |
|----------|---------|---------|
| `process_new_photo` | Graph API webhook (OneDrive change notification) | Extract EXIF, create metadata, generate thumbnail |
| `whatsapp_webhook` | HTTP (Twilio webhook) | Receive WhatsApp photos, save to OneDrive |
| `admin_api` | HTTP | CRUD for metadata, visibility toggle, settings |
| `tablet_sync_api` | HTTP | Serve photo list + metadata to tablet, delta sync |
| `refresh_subscription` | Timer (daily) | Renew Graph API change notification subscriptions |

**Why Azure?**
- Natural fit with OneDrive / Microsoft Graph API
- Azure Functions free tier: 1M executions/month — more than enough
- Cosmos DB free tier included
- Single ecosystem, single billing

### 2.7 Display: Android Tablet App

**Kotlin + Jetpack Compose** application with these features:

#### Core Features
- **Slideshow mode**: Full-screen photos, configurable advancement (10s–5min)
- **Overlay**: Caption, description, date, location — semi-transparent at bottom, auto-hides
- **Transitions**: Fade, slide, ken-burns effect (configurable)
- **Order modes**: Newest first, random, chronological, favorites
- **Local cache**: Synced photos stored locally; works during WiFi outages
- **Auto-start on boot**: Launches directly into slideshow
- **Screen dimming**: Time-based (dim at night, bright during day)

#### Touch Controls (Optional)
- Tap right/left: next/previous photo
- Swipe up: show photo details (caption, date, location, who uploaded)
- Swipe down: hide overlay
- Long press: mark as favorite / hide photo
- Double tap: pause slideshow

#### Sync
- Polls backend API every N minutes (configurable, default: 5 min)
- Downloads new photos in background
- Delta sync: only fetches changes since last sync
- Respects `visible` flag from metadata (admin can hide photos)

#### Kiosk Mode
- Locks tablet to this app (Android screen pinning / device owner mode)
- Prevents accidental exits
- Hides status bar and navigation bar
- Prevents screen timeout

#### Remote Configuration
- Reads `settings.json` from OneDrive `/FamilyFrame/config/`
- Slideshow timing, transition style, display order, night mode schedule
- Admin can change settings remotely — no need to touch grandma's tablet

### 2.8 Admin Interface (Phase 2)

Simple **web app** (Vue.js or React, hosted as Azure Static Web App):

- View all uploaded photos with metadata
- Edit captions, descriptions
- Hide/show photos (moderation)
- Manage family members (who can upload)
- Configure slideshow settings
- View upload statistics
- Language: German UI

---

## 3. Tech Stack Summary

| Layer | Technology | Cost |
|-------|-----------|------|
| Photo Storage | OneDrive (M365 Family, already owned) | €0 |
| Metadata DB | Azure Cosmos DB (free tier) | €0 |
| Backend | Azure Functions (Python, free tier) | €0 |
| Email Ingestion | Power Automate (included in M365) | €0 |
| WhatsApp (Phase 2) | Twilio WhatsApp API | ~€2-5/month |
| Admin Web App (Phase 2) | Azure Static Web Apps (free tier) | €0 |
| Display App | Kotlin / Jetpack Compose | €0 |
| Tablet | Samsung Galaxy Tab A9+ or similar | ~€250 one-time |
| Tablet Stand | Wall mount or desk stand | ~€20-40 one-time |

**Estimated recurring cost: €0-5/month** (essentially free until WhatsApp is added)

---

## 4. Hardware Recommendation

### Tablet: Samsung Galaxy Tab A9+ (WiFi)

- 11" IPS display, 1920x1200, good viewing angles
- Sufficient performance for a slideshow app
- Good WiFi support
- USB-C charging (can be permanently plugged in)
- ~€230-270
- Alternative: Lenovo Tab M11 (~€200), similar specs

### Accessories
- **Tablet stand**: Adjustable desk stand with charging pass-through (~€20-30)
- **OR Wall mount**: VESA-compatible tablet wall mount (~€30-40)
- **Always-on charging**: Standard USB-C charger, always plugged in

### Battery Considerations
- Modern tablets handle permanent charging well (they stop at ~80% and run on AC)
- Enable "always on display" or disable screen timeout in developer settings
- The app handles screen dimming for nighttime

---

## 5. Security & Privacy

- **OneDrive sharing**: Use M365 family sharing — photos stay within the family's Microsoft tenant
- **Azure Functions**: Secured with function keys (not publicly accessible)
- **Tablet API access**: Authenticated via a device token stored on the tablet
- **No photos on third-party servers** (except Twilio for WhatsApp — transient, auto-deleted)
- **Email**: Shared mailbox in M365 — no external email provider needed
- **Admin access**: Protected by Microsoft SSO (M365 account)

---

## 6. Implementation Phases

### Phase 1: MVP (Core Loop) — ~2-3 weeks of development

**Goal**: Family can upload via OneDrive app, grandma sees photos on the tablet.

1. **Set up Azure infrastructure**
   - Azure Function App (Python, Consumption plan)
   - Cosmos DB account (free tier)
   - Register Microsoft Graph API application (Azure AD)

2. **OneDrive integration**
   - Create shared folder `/FamilyFrame/` and share with family
   - Implement Graph API webhook for change notifications
   - `process_new_photo` function: EXIF extraction, metadata creation, thumbnail generation

3. **Tablet Sync API**
   - `tablet_sync_api` function: list photos with metadata, support delta sync
   - Authentication via device token

4. **Android App v1**
   - Slideshow with basic transitions (fade)
   - Photo sync from backend API
   - Local caching
   - Full-screen kiosk mode
   - Caption + date overlay
   - Basic touch controls (tap to advance)
   - Auto-start on boot
   - German UI

5. **Buy & set up tablet**
   - Install app
   - Configure kiosk mode
   - Set up at grandma's house

### Phase 2: Email Upload — ~1 week

6. **Email channel**
   - Create shared mailbox in M365
   - Build Power Automate flow (email → OneDrive)
   - Test with family members

### Phase 3: Polish & Configuration — ~1 week

7. **Remote configuration**
   - `settings.json` in OneDrive, read by tablet app
   - Configurable: slideshow timing, transitions, order, night mode

8. **App improvements**
   - Ken Burns effect
   - Location display (reverse geocoding)
   - Multiple display order modes
   - Night mode / screen dimming schedule
   - Smoother transitions and animations

### Phase 4: WhatsApp Upload — ~1-2 weeks

9. **WhatsApp channel**
   - Set up Twilio account + WhatsApp sender
   - Implement `whatsapp_webhook` Azure Function
   - Share WhatsApp number with family

### Phase 5: Admin Interface — ~2 weeks

10. **Admin web app**
    - Photo management (view, edit metadata, hide/show)
    - Settings management
    - User management
    - Upload statistics

### Phase 6: Future Enhancements (Backlog)

- Multi-language support (beyond German)
- Multiple frames (second display for other family members)
- Photo albums / themed slideshows
- Anniversary/birthday photo highlights (auto-curate by date)
- Video clip support (short clips, <30s)
- Reactions (family members can "heart" photos from their phones)
- Ambient light sensor integration (auto-brightness)
- Web upload portal (for family members who don't want OneDrive/Email/WhatsApp)

---

## 7. Project Structure (Repository)

```
Remote-Picture-Frame/
├── README.md
├── PLAN.md                          ← this file
├── backend/
│   ├── requirements.txt
│   ├── host.json                    ← Azure Functions config
│   ├── local.settings.json          ← local dev settings (gitignored)
│   ├── process_new_photo/
│   │   ├── __init__.py
│   │   └── function.json
│   ├── tablet_sync_api/
│   │   ├── __init__.py
│   │   └── function.json
│   ├── whatsapp_webhook/
│   │   ├── __init__.py
│   │   └── function.json
│   ├── admin_api/
│   │   ├── __init__.py
│   │   └── function.json
│   ├── refresh_subscription/
│   │   ├── __init__.py
│   │   └── function.json
│   └── shared/
│       ├── onedrive.py              ← Graph API helpers
│       ├── metadata.py              ← Cosmos DB helpers
│       └── exif_utils.py            ← EXIF extraction
├── android/
│   └── FamilyFrame/                 ← Android Studio project
│       ├── app/
│       │   └── src/main/
│       │       ├── java/de/familyframe/
│       │       │   ├── MainActivity.kt
│       │       │   ├── slideshow/
│       │       │   ├── sync/
│       │       │   ├── cache/
│       │       │   ├── config/
│       │       │   └── ui/
│       │       └── res/
│       ├── build.gradle.kts
│       └── settings.gradle.kts
├── admin-web/                       ← Phase 5
│   ├── package.json
│   └── src/
├── power-automate/
│   └── email-to-onedrive-flow.md    ← Step-by-step setup guide
├── docs/
│   ├── setup-azure.md               ← Azure setup guide
│   ├── setup-tablet.md              ← Tablet configuration guide
│   ├── setup-onedrive.md            ← OneDrive sharing setup
│   └── family-guide-de.md           ← German user guide for family
└── infrastructure/
    └── bicep/                       ← Azure infrastructure as code
        └── main.bicep
```

---

## 8. Open Decisions

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | Android app: native (Kotlin) vs. PWA in kiosk Chrome | Native gives better kiosk control, smoother animations. PWA is faster to develop. | **Native Kotlin** — better UX for a device that runs 24/7 |
| 2 | Thumbnail generation: in Azure Function vs. on tablet | Azure saves bandwidth; tablet-side is simpler | **Azure Function** — tablets with limited bandwidth benefit |
| 3 | Tablet-to-backend communication: polling vs. push (FCM) | Polling is simpler; FCM gives instant updates | **Polling** (Phase 1), add FCM later if needed |
| 4 | OneDrive monitoring: Graph webhooks vs. periodic polling | Webhooks are near-real-time; polling is simpler but delayed | **Webhooks** — photos appear on frame within minutes |
| 5 | Admin web app framework | Vue.js, React, Svelte | Decide in Phase 5 |

---

## 9. Success Criteria

- Grandma plugs in the tablet → photos appear. No interaction needed. Ever.
- Family member takes a photo → uploads via OneDrive/Email/WhatsApp → photo appears on grandma's frame within 5 minutes
- System runs maintenance-free for months at a time
- Monthly cost stays under €5
