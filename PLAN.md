# Remote Picture Frame - Project Plan

## Vision

A digital picture frame for grandma. Family members (~20 people) upload photos from their phones via multiple channels. Grandma's display shows them automatically — zero interaction required, but touch controls available. Ease of use is the top priority.

---

## Implementation Paths

Three approaches, from near-zero-code to fully custom. They can be adopted incrementally — start with Path A, evolve to B or C if needed.

### Hardware: Raspberry Pi USB Gadget + Samsung TV

All paths use the same display hardware:
- **Raspberry Pi Zero 2 W** (~€20) plugged into grandma's Samsung TV USB port
- RPi emulates a USB mass storage device — TV sees it as a normal USB drive
- TV's built-in media player shows photos as slideshow (grandma already knows how to use this!)
- RPi connects to WiFi and syncs photos from cloud storage in the background
- Powered by the TV's USB port — no extra cables
- Grandma uses her existing Samsung TV remote

```
Family uploads photos          Cloud sync              Display
─────────────────────        ─────────────           ──────────────

OneDrive shared folder                                RPi Zero 2 W
  (or Google Drive)       →  RPi syncs via WiFi  →   emulates USB drive  →  Samsung TV
                             (rclone, cron job)       with photos             built-in
                                                                              slideshow
```

### Cloud Storage: OneDrive (recommended)

**Google Photos is NOT viable** — Google removed third-party API read access in March 2025. rclone can no longer download photos from Google Photos albums.

| Service | rclone sync | Free storage | Upload friction | Verdict |
|---|---|---|---|---|
| **OneDrive** | Works perfectly | **1 TB (existing M365)** | Low (shared folder link, no account needed) | **Recommended** |
| **Google Drive** | Works perfectly | 15 GB | Low (shared folder link, no account needed) | Good alternative |
| Google Photos | **Broken** (API removed March 2025) | 15 GB | Low | NOT VIABLE |
| Dropbox | Works | 2 GB (too small) | Medium (account needed) | Poor |
| iCloud | No API / no rclone | 5 GB | Apple-only | NOT VIABLE |
| Amazon Photos | No third-party API | Unlimited w/ Prime | App required | NOT VIABLE |

**OneDrive wins:** existing M365 subscription with 1 TB, rclone syncs perfectly, family uploads via shared folder link (no Microsoft account needed).

**Google Drive** is a viable alternative if starting fresh (15 GB free, same rclone support, same upload friction). Could be offered as a user-configurable choice.

### Path A: Minimal setup (near-zero code)

**What you set up:**
1. Share OneDrive folder `/FamilyFrame/photos/` with all family members (link sharing, no account needed)
2. Family uploads photos via OneDrive app or shared link in browser
3. Set up RPi Zero 2 W with rclone to sync from OneDrive → local filesystem → USB gadget
4. Plug RPi into Samsung TV USB port
5. Grandma opens USB media player on TV → slideshow

**What you build:**
- `raspberry-pi/setup.sh` — automated RPi setup: rclone config, USB gadget mode, cron sync job
- A cron job that runs `rclone sync` every N minutes and refreshes the USB disk image

**What you get:**
- Auto-updating slideshow on grandma's existing TV
- Family uploads via OneDrive app, shared link, or drag-and-drop in browser
- Grandma navigates folders/photos with her existing TV remote
- Full offline support (photos are local on RPi)
- Zero recurring cost (existing M365)

**What you don't get:**
- Smart rotation / weighted slideshow (TV's media player shows in folder order or filename order)
- Captions / overlays (TV shows filename at most)
- WhatsApp upload channel
- Face recognition / person filter
- Birthday highlights
- Admin interface

**Cost:** ~€20 one-time (RPi Zero 2 W) + €0/month

**Effort:** ~1-2 days setup + scripting. Minimal maintenance (rclone is very stable).

### Path B: RPi with custom slideshow (moderate code)

Same hardware as Path A, but instead of relying on the TV's built-in media player, the RPi generates an **optimized slideshow video or image sequence** that includes our smart features.

**Two sub-options:**

#### B1: RPi generates a slideshow video file

- RPi syncs photos from OneDrive via rclone
- A Python script on RPi creates an MP4 slideshow video (using ffmpeg) with:
  - Photos in smart-weighted order (new photos more often, "on this day", birthday highlights)
  - Caption text burned into the video as subtitles or overlay
  - Fade transitions between photos
  - "Neu" / "Vor X Jahren" badges rendered onto frames
- Video file exposed via USB gadget → TV plays it on loop
- Re-generated periodically (e.g. daily at 3 AM) when new photos arrive

**Advantages:** TV just plays a video — maximally simple. All smart logic runs on RPi.
**Limitation:** Not truly interactive — grandma can't filter by person. New photos only appear after next regeneration cycle. Video generation takes time/CPU on a Pi Zero.

#### B2: RPi as HDMI display (not USB gadget)

- RPi connects to TV via HDMI (not USB)
- RPi runs a lightweight slideshow application (e.g. Python + pygame, or fbi/feh for framebuffer)
- Smart rotation, overlays, transitions all rendered by the RPi directly
- Keyboard input from TV remote via HDMI-CEC (using libcec) for person filter / album selection

**Advantages:** Full interactive control, real-time updates, person filter via TV remote.
**Limitation:** Requires HDMI port (not USB), RPi Zero 2 W may be underpowered for smooth rendering (RPi 4 recommended, ~€45-60). Grandma switches TV input to HDMI instead of USB.

**What you get beyond Path A (both sub-options):**
- Smart weighted rotation (new 3x, favorites 2.5x, "on this day" 4x, birthday 3x)
- Captions and date/location overlay
- Birthday highlights
- "Neu" / "Vor X Jahren" badges
- B2 only: TV remote navigation for person filter / albums

**Cost:** ~€20 (B1, Pi Zero) or ~€50-70 (B2, Pi 4 + case)

**Effort:** ~1-2 weeks development.

### Path C: Full custom system with cloud backend

Everything from the original plan: IBM Cloud Functions backend, multiple upload channels (WhatsApp, web upload page, OneDrive, email), Azure Face API, admin interface. Display via RPi (HDMI, Path B2 style) or PWA on tablet/streaming stick.

**What you get beyond Path B:**
- WhatsApp as upload channel (easiest for non-tech family members)
- Web upload page with PIN (works for guests, no app needed)
- Face recognition with person-based filtering
- Full admin interface with photo moderation
- Email upload channel
- Multiple display device support (tablet, RPi, streaming stick)

**Cost:** ~€20-270 one-time (display device) + €0/month (all free tiers)

**Effort:** ~6-8 weeks development. Full maintenance responsibility.

### Comparison

| | Path A | Path B1 | Path B2 | Path C |
|---|---|---|---|---|
| **Hardware** | RPi Zero USB | RPi Zero USB | RPi 4 HDMI | RPi / tablet / stick |
| **Cost** | ~€20 | ~€20 | ~€50-70 | ~€20-270 |
| **Setup time** | 1-2 days | 1-2 weeks | 1-2 weeks | 6-8 weeks |
| **Maintenance** | Minimal | Low | Low | Medium |
| **Slideshow** | TV built-in (basic) | Smart (pre-rendered) | Smart (real-time) | Smart (real-time) |
| **Upload method** | OneDrive link/app | OneDrive link/app | OneDrive link/app | WhatsApp, web, OneDrive, email |
| **Captions/overlay** | No | Yes (burned in) | Yes (live) | Yes (live) |
| **Birthday highlights** | No | Yes | Yes | Yes |
| **Person filter** | No | No | Yes (TV remote) | Yes |
| **New photo delay** | ~5 min (rclone sync) | Next regen cycle | ~5 min (rclone sync) | ~5 min |
| **WhatsApp upload** | No | No | No | Yes |
| **Grandma's experience** | USB media player (familiar!) | USB video (familiar!) | HDMI input (new) | Varies |

### Recommended strategy

**Start with Path A this weekend.** RPi Zero 2 W + rclone + USB gadget. Grandma sees auto-updating photos on her TV using the same USB media player she already uses for videos. Family uploads via OneDrive shared link.

**If the family wants captions and smart features:** Move to Path B1 (generate slideshow video on RPi) or B2 (RPi as HDMI display with interactive controls).

**Only go to Path C** if WhatsApp upload or full admin control is genuinely needed.

### Previous options (still viable for other setups)

**Chromecast with Google TV / Google TV Streamer / Amazon Fire TV Stick:**
These remain good options if grandma gets a newer TV or a second display is needed elsewhere. The Chromecast HD (~€30) or Google TV Streamer (~€100) with Google Photos Ambient Mode provides a zero-code slideshow. Fire TV Stick (~€25-35) with Amazon Photos is best if the family has Prime. However, for grandma's current Samsung TV with existing USB workflow, the RPi USB gadget approach is simpler and cheaper.

---

## 1. Architecture Overview (Path C — Full Custom)

```
Upload Channels              Processing                Storage            Display
───────────────             ────────────              ─────────          ─────────

OneDrive App ──────────────────────────────────────→ OneDrive  ←──sync──→ Any Device
(direct upload)                                      Shared       (Graph   - Android Tablet
                                                     Folder       API)     - iPad
Email ──→ Power Automate ──→ Save to OneDrive ────→ /Family               - Raspberry Pi
          (M365 included)    + extract caption        Frame/
                                                                   ┌──────────────┐
WhatsApp ──→ Meta Cloud API ──→ IBM Cloud Function ──→ OneDrive           │  PWA          │
(Phase 2)    Webhook     (process + save)                         │  Slideshow    │
                                                                   │  + Captions   │
                                                Metadata DB        │  + Date/Loc   │
                                                (IBM Cloudant      │  + Touch Nav  │
                                                 Lite plan)        └──────────────┘
```

### Core Principles

1. **OneDrive as Single Source of Truth** — the family already has 1TB via M365. Every upload channel funnels photos into one shared OneDrive folder.
2. **IBM Cloud for compute** — serverless functions and database on IBM Cloud (free tiers).
3. **PWA for the display** — one web app codebase runs on Android tablets, iPads, and Raspberry Pi alike.

---

## 2. Components

### 2.1 OneDrive Shared Folder Structure & Isolation

The family OneDrive is used for other purposes. To ensure family members uploading photos **never see other OneDrive content**, we use one of two isolation strategies:

**Strategy A — Shared folder (simple)**:
Create `/FamilyFrame/` in the main OneDrive and share *only that folder* with family members. They receive a "Shared with me" link and can only access this one folder. The rest of the OneDrive is invisible to them.

**Strategy B — Dedicated account (strongest isolation, recommended)**:
Create a free Microsoft account (e.g. `familyframe@outlook.com`) used exclusively for this app. It gets 5 GB free OneDrive storage — sufficient for thousands of photos. Family members share photos *into this account's folder*. Complete separation from any personal/family OneDrive data. The backend's Graph API app registration is scoped to this account only.

```
/FamilyFrame/                       ← shared with family (or in dedicated account)
  /photos/                          ← upload target (family drops photos here)
    /Anna/                          ← auto-created: backend sorts by uploader
    /Thomas/                        ← auto-created: backend sorts by uploader
    /Urlaub-Kroatien-2026/          ← optional: family can create event folders
  /config/
    settings.json                   ← slideshow settings, synced to display
```

**Folder organization**: Family uploads to `/photos/` (flat, simple). The backend automatically moves each photo into a subfolder named after the uploader (detected via OneDrive metadata). Family members can also create their own event/occasion subfolders — photos in those are left in place. The display shows all photos from all subfolders equally.

> **Note**: With Strategy B, the 5 GB limit can be extended by purchasing a standalone Microsoft 365 Basic plan (~€2/month for 100 GB) if needed later. For photos at ~3-5 MB each, 5 GB holds ~1000-1500 photos.

### 2.2 Metadata Storage (IBM Cloudant - Lite Plan)

IBM Cloudant is a managed CouchDB service. Lite plan: 1 GB storage, 20 reads/sec, 10 writes/sec — more than enough.

Each photo gets a metadata document:

```json
{
  "_id": "abc123",
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
  "tags": [],
  "thumbnail_url": "https://..."
}
```

**Why a separate DB and not just OneDrive file properties?**
- OneDrive file descriptions are limited and not easily queryable
- Enables filtering, search, and admin features later
- Consistent metadata regardless of upload channel
- Cloudant views allow efficient queries (e.g. "newest 50 photos", "photos by Maria")

### 2.3 Upload Channel: OneDrive App (Built-in)

- Family members install OneDrive on their phones (most will already have it)
- They upload photos to the shared `/FamilyFrame/photos/` folder
- An **IBM Cloud Function** monitors the folder via Microsoft Graph API webhooks (change notifications)
- On new photo: extract EXIF data (date, GPS), create metadata record in Cloudant
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
  3. The same IBM Cloud Function picks up the new file and creates the metadata record
- **Bonus**: Works from any device, any platform — just send an email with photos attached

### 2.5 Upload Channel: Web Upload Page (Phase 3)

A simple, mobile-friendly web page where family members can upload photos directly — no app installation, no account needed. Just a link shared in the family WhatsApp group.

- **URL**: e.g. `https://familyframe.example.com/upload` (hosted alongside the PWA on IBM Cloud Object Storage)
- **Features**:
  - Drag & drop or tap to select photos (multiple at once)
  - Caption field (optional)
  - Description field (optional)
  - Name field ("Wer bist du?" — remembered in localStorage)
  - Upload progress indicator
  - Works on any phone browser — no app needed
- **Backend**: Submits to a new `upload_api` IBM Cloud Function that:
  1. Receives the photo + metadata via multipart form upload
  2. Uploads to OneDrive `/FamilyFrame/photos/`
  3. Creates metadata record in Cloudant (caption, description, uploader name)
- **Security**: Protected by a simple shared family code (e.g. a 6-digit PIN) — not public
- **Why this is great**:
  - Lowest friction of all upload channels — just open a link and drop a photo
  - No OneDrive account, no email address, no WhatsApp number needed
  - Works for guests (e.g. visitors at a family gathering)
  - The link can be shared as a QR code printed next to the frame
  - Can be bookmarked on the home screen like an app

### 2.6 Upload Channel: WhatsApp (Phase 4)

- Dedicated WhatsApp number via **Meta WhatsApp Cloud API** (free tier)
- Family members send photos (and optional caption as message text) to this number
- Meta Cloud API webhook → **IBM Cloud Function**:
  1. Verify webhook signature (security)
  2. Download the media from Meta's servers (using the media URL + access token)
  3. Upload to OneDrive `/FamilyFrame/photos/`
  4. Extract caption from message text
  5. Create metadata record
  6. Optional: send a confirmation reply within the 24h conversation window
- **Cost**: €0/month (free tier: 1,000 service conversations/month — more than enough for a family of 20)
- **Setup requirements**:
  - Personal Facebook account (no business needed)
  - Meta Business Portfolio (free, at business.facebook.com)
  - Meta Developer App (free, at developers.facebook.com)
  - A phone number for WhatsApp registration (prepaid SIM, ~€5 one-time)
- **Why Meta Cloud API over Twilio?**
  - Free vs. ~€2-5/month with Twilio
  - Official API, same reliability
  - Direct from Meta — no middleman
  - 1,000 free conversations/month (user-initiated = family sends photo = free)

### 2.7 Backend: IBM Cloud Functions (Serverless)

All backend logic runs as IBM Cloud Functions (Python, based on Apache OpenWhisk):

| Function | Trigger | Purpose |
|----------|---------|---------|
| `process_new_photo` | HTTP (Graph API webhook) | Extract EXIF, create metadata, generate thumbnail |
| `upload_api` | HTTP (multipart form POST) | Receive photos from web upload page, save to OneDrive |
| `whatsapp_webhook` | HTTP (Meta WhatsApp Cloud API webhook) | Receive WhatsApp photos, save to OneDrive |
| `admin_api` | HTTP | CRUD for metadata, visibility toggle, settings |
| `display_sync_api` | HTTP | Serve photo list + metadata to display, delta sync |
| `refresh_subscription` | IBM Cloud cron trigger (daily) | Renew Graph API change notification subscriptions |

**Why IBM Cloud?**
- IBM Cloud Functions free tier: 5M executions/month
- Cloudant Lite plan: free
- IBM Cloud Object Storage (for static web hosting): free lite tier
- Microsoft Graph API is a standard REST API — works from any cloud

**IBM Cloud vs. Azure tradeoffs:**
- Azure has tighter OneDrive integration (same ecosystem), but Graph API works identically from IBM Cloud
- IBM Cloud Functions use Apache OpenWhisk (open source) — no vendor lock-in
- Power Automate stays in M365 regardless of which cloud hosts the backend

### 2.8 Display: Progressive Web App (PWA)

A **single web application** that runs on all display platforms:

| Platform | Browser | Kiosk Mode |
|----------|---------|------------|
| Android Tablet | Chrome | Screen Pinning + "Add to Home Screen" |
| iPad | Safari | Guided Access mode |
| Raspberry Pi | Chromium | `--kiosk` flag on startup |

**Tech stack**: TypeScript + Vue.js 3 (lightweight, reactive, good for animations)

#### Core Features
- **Slideshow mode**: Full-screen photos, configurable advancement (10s–5min)
- **Overlay**: Caption, description, date, location — semi-transparent at bottom, auto-hides
- **Transitions**: CSS-based fade, slide, Ken Burns effect (configurable)
- **Order modes**: Newest first, random, chronological, favorites
- **Offline support**: Service Worker caches photos locally; works during WiFi outages
- **Screen wake lock**: Uses Screen Wake Lock API (supported in Chrome/Chromium) to prevent sleep
- **Screen dimming**: CSS-based brightness reduction on schedule (night mode)

#### Touch Controls (Optional)
- Tap right/left edge: next/previous photo
- Swipe up: show photo details (caption, date, location, who uploaded)
- Swipe down: hide overlay
- Long press: mark as favorite / hide photo
- Double tap: pause slideshow

#### Sync
- Polls `display_sync_api` every N minutes (configurable, default: 5 min)
- Downloads new photos in background via Service Worker
- Delta sync: only fetches changes since last sync timestamp
- Respects `visible` flag from metadata (admin can hide photos)
- Photos cached in browser's Cache Storage API (persists across restarts)

#### Remote Configuration
- Fetches `settings.json` from backend API (sourced from OneDrive `/FamilyFrame/config/`)
- Slideshow timing, transition style, display order, night mode schedule
- Admin can change settings remotely — no need to touch grandma's display

#### PWA Advantages over Native App
- **One codebase** for Android, iPad, and Raspberry Pi
- Faster development and iteration (web tech)
- No app store approval needed — just a URL
- Easy updates — deploy new version, all displays auto-update
- Family members can also open it on their phones to preview

#### PWA Limitations & Mitigations
| Limitation | Mitigation |
|-----------|-----------|
| No true auto-start on boot | Android: Fully Kiosk Browser app (~€7, auto-launches URL on boot). RPi: Chromium autostart in systemd. iPad: Guided Access persists across reboots. |
| Wake lock limited in Safari | iPad: Guided Access prevents sleep anyway |
| Less control over system UI | Fullscreen API hides browser chrome; kiosk tools hide system UI |

### 2.9 Admin Interface (Phase 5)

Simple **web app** (Vue.js, same stack as display app), hosted on IBM Cloud Object Storage + CDN:

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
| Metadata DB | IBM Cloudant (Lite plan) | €0 |
| Backend | IBM Cloud Functions (Python) | €0 (free tier) |
| Static Hosting | IBM Cloud Object Storage (PWA + Admin) | €0 (lite tier) |
| Email Ingestion | Power Automate (included in M365) | €0 |
| WhatsApp (Phase 4) | Meta WhatsApp Cloud API (free tier) | €0 (1,000 conv/month free) |
| Display App | PWA (TypeScript + Vue.js 3) | €0 |
| Display Hardware | Android tablet / iPad / Raspberry Pi | €60-300 one-time |

**Estimated recurring cost: €0/month** (all services on free tiers, including WhatsApp)

---

## 4. Hardware Options

### Option A: Android Tablet (Recommended for simplicity)

**Samsung Galaxy Tab A9+ (WiFi)**
- 11" IPS display, 1920x1200, good viewing angles
- Sufficient performance for a PWA slideshow
- USB-C charging (can be permanently plugged in)
- ~€230-270
- Alternative: Lenovo Tab M11 (~€200), similar specs

**Kiosk setup**: Install "Fully Kiosk Browser" (~€7 one-time) — auto-launches the PWA URL on boot, prevents exit, hides system UI, supports screen dimming schedules.

### Option B: iPad (If already available)

- Any iPad with iOS 15+ works
- Use Guided Access (Settings → Accessibility → Guided Access) to lock to Safari
- PWA "Add to Home Screen" for full-screen mode
- Advantage: excellent display quality
- Disadvantage: slightly less kiosk control than Android

### Option C: Raspberry Pi (Budget option / DIY)

**Raspberry Pi 4 (or 5) + Display**
- Pi 4 (4GB): ~€45-60
- Official 7" touchscreen: ~€70 (or third-party 10" IPS: ~€80-100)
- Case + stand: ~€15-20
- Power supply: ~€10
- **Total: ~€140-190**

**Kiosk setup**:
```bash
# Auto-start Chromium in kiosk mode on boot (systemd service)
chromium-browser --kiosk --noerrdialogs --disable-translate \
  --no-first-run --start-fullscreen https://familyframe.example.com
```

- Advantage: cheapest, most customizable, great for a second frame
- Disadvantage: requires initial Linux setup, slightly more maintenance

### Accessories (All Options)
- **Tablet/display stand**: Adjustable desk stand (~€20-30) or wall mount (~€30-40)
- **Always-on power**: Standard charger, always plugged in

### Battery Considerations (Tablets)
- Modern tablets handle permanent charging well (they stop at ~80% and run on AC)
- "Fully Kiosk Browser" on Android has a built-in screen-off schedule
- The PWA handles visual dimming for nighttime

---

## 5. Security & Privacy

- **OneDrive isolation**: Dedicated account or scoped shared folder — family members never see other OneDrive content (see Section 2.1)
- **IBM Cloud Functions**: Secured with API keys (not publicly accessible without token)
- **Display API access**: Authenticated via a device token stored on the display device
- **No photos on third-party servers** (WhatsApp media is hosted by Meta temporarily, downloaded by our function, then only stored in OneDrive)
- **Email**: Shared mailbox in M365 — no external email provider needed
- **Admin access**: Protected by Microsoft SSO (M365 account)
- **PWA served over HTTPS**: IBM Cloud Object Storage with custom domain + TLS
- **CORS**: Backend API restricted to the PWA's origin domain

---

## 6. Remote Administration (Grandma's Device)

Grandma's display must be fully manageable without physical access.

### Layered Remote Management

| Layer | Tool | What it does | Cost |
|-------|------|-------------|------|
| **App settings** | Our PWA + OneDrive `settings.json` | Change slideshow timing, photo order, transitions, night mode schedule — all by editing a JSON file in OneDrive | €0 (built-in) |
| **Kiosk control** | Fully Kiosk Browser (Android) | Built-in web-based remote admin: view live screen, change URL, restart browser, adjust brightness, view device status, wake/sleep screen | Included in €7 license |
| **Full remote control** | TeamViewer QuickSupport | Full remote screen control as if touching the tablet — for troubleshooting, OS updates, app installs | Free (personal use) |
| **Device management** | Google Find My Device | Locate, lock, ring, or wipe the tablet remotely | Free |

### Typical Remote Admin Scenarios

| Scenario | How to handle |
|----------|--------------|
| Change slideshow speed | Edit `settings.json` in OneDrive → display picks up changes within minutes |
| Hide an inappropriate photo | Use admin web app (Phase 5) or directly update Cloudant metadata |
| Tablet screen is black | Open Fully Kiosk Browser remote admin → wake screen, check status |
| Tablet needs OS update | Connect via TeamViewer → walk through update |
| WiFi password changed at grandma's | TeamViewer (if still connected) or physical visit needed |
| App not loading | Fully Kiosk Browser remote admin → clear cache, reload URL |

### Setup (One-Time at Grandma's House)
1. Install **Fully Kiosk Browser** — configure remote admin (set password, enable web server)
2. Install **TeamViewer QuickSupport** — link to your TeamViewer account for unattended access
3. Enable **Google Find My Device** in Android settings
4. Configure **Fully Kiosk Browser** to auto-start the PWA URL on boot
5. Test remote access from home before leaving

---

## 7. Implementation Phases

### Phase 1: MVP (Core Loop) — ~2-3 weeks of development

**Goal**: Family can upload via OneDrive app, grandma sees photos on the display.

1. **Set up IBM Cloud infrastructure**
   - IBM Cloud account + Cloud Functions namespace
   - Cloudant database instance (Lite plan)
   - Register Microsoft Graph API application (Azure AD / Entra ID — required for OneDrive API regardless of cloud)
   - IBM Cloud Object Storage bucket for PWA hosting

2. **OneDrive integration**
   - Create shared folder `/FamilyFrame/` and share with family
   - Implement Graph API webhook for change notifications
   - `process_new_photo` function: EXIF extraction, metadata creation, thumbnail generation

3. **Display Sync API**
   - `display_sync_api` function: list photos with metadata, support delta sync
   - Authentication via device token

4. **PWA Display App v1**
   - Vue.js 3 + TypeScript project
   - Slideshow with fade transitions
   - Photo sync from backend API
   - Service Worker for offline caching
   - Fullscreen mode
   - Caption + date overlay
   - Basic touch controls (tap to advance)
   - German UI

5. **Deploy & set up display**
   - Deploy PWA to IBM Cloud Object Storage
   - Buy tablet (or set up Raspberry Pi)
   - Configure kiosk mode
   - Set up at grandma's house

### Phase 2: Email Upload — ~1 week

6. **Email channel**
   - Create shared mailbox in M365
   - Build Power Automate flow (email → OneDrive)
   - Test with family members

### Phase 3: Web Upload Page & Polish — ~1-2 weeks

7. **Web upload page**
   - Mobile-friendly upload form (drag & drop, caption, name)
   - `upload_api` IBM Cloud Function (receives photos, saves to OneDrive)
   - Protected by a shared family PIN
   - Hosted alongside PWA on IBM Cloud Object Storage
   - Generate QR code for the upload link
   - Share link in family WhatsApp group

8. **Remote configuration**
   - `settings.json` in OneDrive, served via API
   - Configurable: slideshow timing, transitions, order, night mode

9. **App improvements**
   - Ken Burns effect (CSS animations)
   - Location display (reverse geocoding via Nominatim / OpenStreetMap — free)
   - Multiple display order modes
   - Night mode / screen dimming schedule
   - Smoother transitions and animations
   - Swipe gestures

### Phase 4: WhatsApp Upload — ~1-2 weeks

10. **WhatsApp channel (Meta WhatsApp Cloud API — free)**
   - Create Meta Business Portfolio (free, no real business needed)
   - Create Meta Developer App + add WhatsApp product
   - Register a phone number (prepaid SIM, ~€5 one-time)
   - Configure webhook URL → IBM Cloud Function `whatsapp_webhook`
   - Implement `whatsapp_webhook`: verify signature, download media, save to OneDrive
   - Test with family, share the WhatsApp number

### Phase 5: Admin Interface — ~2 weeks

11. **Admin web app**
    - Vue.js app (same stack as display PWA)
    - Photo management (view, edit metadata, hide/show)
    - Settings management
    - User management
    - Upload statistics
    - Hosted on IBM Cloud Object Storage

### Phase 6: Face Recognition (Azure Face API)

Automatic identification of who is **in** each photo, so grandma can filter by person.

**Architecture:**
- Azure AI Face service (free F0 tier: 30K transactions/month)
- Person Group trained with 3-6 sample face images per family member
- `process_new_photo` runs face detection + identification on each upload
- Recognized names stored in `people[]` field in Cloudant metadata
- Display person filter uses `people` (who's in the photo) with `uploaded_by` as fallback

**Admin workflow:**
1. Admin → "Gesichter" tab → create person group (one-time)
2. Add each family member → upload 3-6 sample face photos
3. Click "Modell trainieren" → model trains in seconds
4. All new photos are automatically scanned for recognized faces

**Components:**
- `backend/shared/face_recognition.py` — Azure Face API client
- `backend/packages/admin_api` — face management endpoints (setup, add/remove persons, add samples, train)
- `admin-web/src/components/FaceManager.vue` — admin UI for face training
- Display: PersonFilter shows recognized people names, overlay shows who's in the photo

### Phase 7: Future Enhancements (Backlog)

- **Raspberry Pi hardware & display deep-dive**:
  Research and document concrete RPi picture frame builds:
  - **Display options**: Official 7" (800x480, too low-res?), Waveshare 10.1" IPS (1280x800, HDMI), Pimoroni HyperPixel 4.0 (4" high-DPI, too small), generic 10-15" HDMI IPS monitors (1080p, best image quality but need separate power), repurposed old laptop screens with HDMI controller boards (~€20-30).
  - **Cases / frames**: 3D-printed picture frame enclosures (Thingiverse), IKEA RIBBA frame hack (mount screen behind photo frame mat), commercial RPi display cases (e.g. SmartiPi Touch), wall-mount VESA brackets for larger displays, custom wood frame.
  - **Power**: Single USB-C powering both RPi and display (official 7" only), or two power cables (RPi + HDMI display). Consider smart plug for scheduled on/off as alternative to night mode dimming.
  - **RPi model**: RPi 4 (2GB sufficient for Chromium kiosk), RPi 5 (overkill but future-proof), RPi Zero 2 W (might struggle with Chromium + image rendering).
  - **Recommended builds**:
    - Budget (~€100): RPi 4 2GB + official 7" touchscreen + SmartiPi case
    - Quality (~€180): RPi 4 4GB + Waveshare 10.1" IPS HDMI + 3D-printed frame
    - Premium (~€250): RPi 5 + 13-15" 1080p IPS HDMI monitor + IKEA frame hack
  - **Setup automation**: Extend `raspberry-pi/setup.sh` with display auto-detection, screen rotation config, HDMI settings for non-standard displays, touch calibration.

- **Raspberry Pi: local OneDrive sync via rclone** (replaces image proxy for RPi deployments):
  Mount OneDrive directly on the RPi with `rclone mount onedrive:/FamilyFrame/photos /home/pi/photos --vfs-cache-mode full`.
  Serve images via a local nginx or Python HTTP server (`http://localhost:8080/photos/...`).
  The display PWA points to localhost for images instead of Microsoft download URLs.
  Benefits: perfect offline support, no Graph API download calls, instant image loading, no backend egress.
  Metadata (captions, people, favorites) still comes from Cloudant via IBM Cloud Functions — only the image delivery changes.
  Update `raspberry-pi/setup.sh` to install rclone, configure OneDrive remote, set up systemd service for mount + local HTTP server.
  Does NOT apply to Android/iPad tablets (PWA can't access local files there — keep current approach or image proxy).
- **Image proxy** (for tablet deployments): Proxy photo downloads through backend instead of exposing pre-authenticated Microsoft URLs directly. Benefits: stable cacheable URLs, better service worker caching, credentials stay server-side, fewer Graph API calls. Trade-off: adds latency and IBM Cloud egress.
- Multi-language support (beyond German)
- Multiple frames (second display for other family members — just open the URL!)
- Video clip support (short clips, <30s)
- Reactions (family members can "heart" photos from their phones)
- Ambient light sensor integration (auto-brightness, where supported)
- Push notifications to display via Web Push API (instant photo updates)

- **Alternative backend: Google Photos instead of OneDrive**
  Replace OneDrive with Google Photos as the photo storage layer. This would significantly simplify the architecture by leveraging Google's built-in EXIF extraction, thumbnail generation, and face recognition.

  **How it would work:**
  - One dedicated Google account (e.g. `familyframe@gmail.com`) owns all albums
  - Family members add photos via shared album links (no Google account needed to add)
  - Family can create event albums directly in Google Photos ("Urlaub Kroatien 2026")
  - Our backend reads photos via Google Photos API (`mediaItems.search()`, `albums.list()`)
  - WhatsApp webhook uploads to Google Photos via API instead of OneDrive
  - Web upload page uploads to Google Photos via API instead of OneDrive

  **What we'd eliminate:**
  - All OneDrive/Graph API code (onedrive.py, webhook subscriptions, refresh_subscription)
  - Azure Face API integration (Google does face grouping natively)
  - EXIF extraction code (Google extracts metadata automatically)
  - Thumbnail generation (Google provides multiple sizes via `baseUrl` parameter)

  **What we'd keep:**
  - IBM Cloud backend (lighter — display sync, WhatsApp webhook, upload API, admin)
  - Cloudant (custom metadata overlay: favorites, birthday config, smart rotation state, captions)
  - Display PWA with smart rotation, overlays, person filter, touch controls
  - WhatsApp upload channel
  - Admin interface (lighter)

  **Key limitations of Google Photos API:**
  - **No person/face query via API** — Google removed person-based search from the API for privacy. Workarounds: (a) family creates per-person albums manually, (b) we keep lightweight face tagging ourselves, or (c) accept this limitation
  - **Read-only for favorites** — API can't mark favorites; we track our own in Cloudant
  - **Shared album API access** — works well when the owning account authorizes our app; contributors don't need API access
  - **Rate limits** — 10,000 requests/day (free), more than enough for a family frame
  - **Storage** — 15 GB free (shared with Gmail/Drive), ~€2/month for 100 GB if needed

  **Cost comparison:**
  | | Current (OneDrive) | Google Photos |
  |---|---|---|
  | Photo storage | €0 (existing M365 1TB) | €0 (15 GB free) or €2/mo (100 GB) |
  | Face recognition | €0 (Azure free tier, 30K/mo) | €0 (built-in, but no API access) |
  | Backend complexity | High (webhooks, subscriptions, EXIF, thumbnails) | Low (Google handles most of it) |
  | Vendor lock-in | Microsoft | Google |

  **Decision**: Document as alternative. Current OneDrive approach works and uses existing M365 subscription. Google Photos is a strong option if starting fresh or if OneDrive integration proves too complex in practice. Could also be offered as a user-configurable backend choice.

- **Display on Samsung Smart TV (or any smart TV)**
  Instead of a dedicated tablet or Raspberry Pi, use an existing smart TV as the display.

  **Recommended approach: Chromecast with Google TV (~€35) or Amazon Fire TV Stick (~€35)**
  - Plug into any TV's HDMI port
  - Install a kiosk/fullscreen browser (e.g. "Fully Kiosk Browser" on Fire TV, or sideload on Chromecast)
  - Auto-launch our PWA URL on boot
  - HDMI-CEC can auto-power the TV on/off on schedule
  - Cheapest, most reliable method — works with ANY TV that has HDMI

  **Alternative: Samsung TV's built-in browser**
  - Open PWA URL in Samsung Internet browser → go fullscreen
  - Works but less reliable: browser may close after updates, no auto-start on boot, TV standby interrupts

  **Samsung "The Frame" TV**
  - Designed as a digital picture frame, but requires manual photo upload via SmartThings app
  - No URL/API-based slideshow — not compatible with our PWA approach
  - Samsung Art Store subscription not needed (own photos are free)

  **Integration with display PWA:**
  - No code changes needed — our PWA runs in any browser
  - Screen Wake Lock API works in Chromium-based browsers on streaming sticks
  - Night mode dimming works via CSS (or HDMI-CEC power off)

- **TV remote navigation (for Smart TV / streaming stick deployments)**
  Grandma uses her existing TV remote to navigate the PWA — no touchscreen, no smartphone, no extra remote needed. HDMI-CEC passes the TV remote's directional pad and OK/Back buttons through to the streaming stick's browser as standard keyboard events. This works out of the box on most Samsung (and other) TV remotes.

  **Key mapping:**
  | TV Remote Button | PWA Action |
  |---|---|
  | Left / Right | Previous / next photo |
  | Up | Open navigation menu (person filter / albums) |
  | Down | Close menu / hide overlay |
  | OK / Enter | Select highlighted item in menu |
  | Back | Return to slideshow from menu |

  **Navigation menu** (full-screen overlay, large text readable from couch distance):
  - List of people (from `settings.family_members` or recognized faces)
  - List of albums
  - "Alle Fotos" option to clear any filter
  - Arrow up/down highlights items, OK selects, Back dismisses
  - Looks and feels like a standard TV menu — no learning curve for grandma

  **Implementation:**
  - Add `keydown` event listeners to the display PWA alongside existing touch handlers
  - New `NavigationMenu.vue` component: full-screen overlay with focus-based item selection
  - Only directional pad + OK + Back are needed — these are the most reliably passed through HDMI-CEC across TV brands
  - Same PWA codebase, no separate build — menu simply doesn't appear on touch devices unless invoked via remote

---

## 8. Project Structure (Repository)

```
Remote-Picture-Frame/
├── README.md
├── PLAN.md                          ← this file
├── backend/
│   ├── requirements.txt
│   ├── packages/
│   │   ├── process_new_photo/
│   │   │   └── __main__.py          ← IBM Cloud Function entry point
│   │   ├── display_sync_api/
│   │   │   └── __main__.py
│   │   ├── upload_api/
│   │   │   └── __main__.py          ← receives web upload form submissions
│   │   ├── whatsapp_webhook/
│   │   │   └── __main__.py
│   │   ├── admin_api/
│   │   │   └── __main__.py
│   │   └── refresh_subscription/
│   │       └── __main__.py
│   ├── shared/
│   │   ├── onedrive.py              ← Graph API helpers
│   │   ├── metadata.py              ← Cloudant helpers
│   │   └── exif_utils.py            ← EXIF extraction
│   └── deploy.sh                    ← IBM Cloud CLI deployment script
├── display-app/
│   ├── package.json
│   ├── vite.config.ts               ← Vite build config
│   ├── tsconfig.json
│   ├── index.html
│   ├── public/
│   │   ├── manifest.json            ← PWA manifest
│   │   └── sw.js                    ← Service Worker
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── components/
│       │   ├── Slideshow.vue
│       │   ├── PhotoOverlay.vue
│       │   └── TouchControls.vue
│       ├── composables/
│       │   ├── useSync.ts           ← Photo sync logic
│       │   ├── useSlideshow.ts      ← Slideshow state machine
│       │   └── useSettings.ts       ← Remote config
│       ├── services/
│       │   ├── api.ts               ← Backend API client
│       │   └── cache.ts             ← Cache Storage management
│       └── types/
│           └── index.ts
├── upload-page/                     ← Phase 3: simple web upload form
│   ├── index.html                   ← single-page upload form (mobile-friendly)
│   ├── style.css
│   └── upload.js
├── admin-web/                       ← Phase 5
│   ├── package.json
│   └── src/
├── power-automate/
│   └── email-to-onedrive-flow.md    ← Step-by-step setup guide
├── raspberry-pi/
│   ├── setup.sh                     ← Automated RPi kiosk setup script
│   └── README.md
├── docs/
│   ├── setup-ibmcloud.md            ← IBM Cloud setup guide
│   ├── setup-display.md             ← Display device configuration guide
│   ├── setup-onedrive.md            ← OneDrive sharing setup
│   └── family-guide-de.md           ← German user guide for family
└── infrastructure/
    └── ibmcloud/
        └── deploy.sh                ← IBM Cloud infrastructure setup
```

---

## 9. Open Decisions

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | PWA framework | Vue.js 3, React, Svelte | **Vue.js 3** — lightweight, great for animations, Composition API fits well |
| 2 | Thumbnail generation | In IBM Cloud Function vs. on display device | **IBM Cloud Function** — saves bandwidth, consistent sizing |
| 3 | Display-to-backend communication | Polling vs. Web Push API | **Polling** (Phase 1), add Web Push later if near-instant updates needed |
| 4 | OneDrive monitoring | Graph API webhooks vs. periodic polling | **Webhooks** — photos appear on frame within minutes |
| 5 | Reverse geocoding for locations | Nominatim (free, OSM), Google Maps API (paid), offline DB | **Nominatim** — free, no API key needed, sufficient accuracy |
| 6 | Display device for grandma | Android tablet, iPad, Raspberry Pi | **Android tablet** for grandma (easiest kiosk setup), RPi for future frames |
| 7 | Kiosk browser (Android) | Fully Kiosk Browser, Chrome + Screen Pinning, custom launcher | **Fully Kiosk Browser** — purpose-built, €7, excellent features |

---

## 10. Success Criteria

- Grandma plugs in the display → photos appear. No interaction needed. Ever.
- Family member takes a photo → uploads via OneDrive/Email/WhatsApp → photo appears on grandma's frame within 5 minutes.
- A second family member wants a frame → just open the URL on any device. Done.
- System runs maintenance-free for months at a time.
- Monthly cost: €0 (all free tiers).
