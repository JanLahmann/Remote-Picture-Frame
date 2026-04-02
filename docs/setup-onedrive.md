# OneDrive Einrichtung

Diese Anleitung beschreibt die Einrichtung des OneDrive-Speichers fuer FamilyFrame.

---

## 1. Entscheidung: Eigenes Konto oder geteilter Ordner?

### Option A: Dediziertes Microsoft-Konto (empfohlen)

Ein separates kostenloses Microsoft-Konto nur fuer FamilyFrame. Familie sieht nie andere Daten.

**Vorteile:**
- Vollstaendige Isolation — kein Risiko, dass jemand fremde Dateien sieht
- Eigener 5 GB OneDrive-Speicher (reicht fuer ~1000-1500 Fotos)
- Kann spaeter auf 100 GB erweitert werden (~2 EUR/Monat)

**Einrichtung:**
1. Gehe zu https://outlook.live.com → Konto erstellen
2. Erstelle z.B. `familyframe.mustermann@outlook.com`
3. Melde dich an und gehe zu https://onedrive.live.com
4. Erstelle den Ordner `/FamilyFrame/photos/`
5. Erstelle den Ordner `/FamilyFrame/config/`

### Option B: Geteilter Ordner im bestehenden OneDrive

Einen Unterordner im bestehenden Family-OneDrive freigeben.

**Vorteile:**
- Kein zusaetzliches Konto
- Nutzt den bestehenden 1 TB Speicher

**Einrichtung:**
1. Melde dich bei https://onedrive.live.com mit deinem M365-Konto an
2. Erstelle den Ordner `/FamilyFrame/photos/`
3. Erstelle den Ordner `/FamilyFrame/config/`

---

## 2. Ordnerstruktur erstellen

```
FamilyFrame/
  photos/                          ← Upload-Ordner (alle laden hier hoch)
    Anna/                          ← automatisch erstellt vom Backend
    Thomas/                        ← automatisch erstellt vom Backend
    Urlaub-Kroatien-2026/          ← optional: Familie kann Event-Ordner erstellen
  config/
    settings.json                  ← Einstellungen fuer den Bilderrahmen
```

### Wie funktioniert das?

- **Upload**: Alle Familienmitglieder laden Fotos direkt in `/FamilyFrame/photos/` hoch
- **Auto-Sortierung**: Das Backend erkennt den Uploader (ueber OneDrive-Metadaten) und verschiebt das Foto automatisch in einen Unterordner mit dem Namen der Person (z.B. `/photos/Anna/`)
- **Event-Ordner**: Familienmitglieder koennen optional eigene Unterordner erstellen (z.B. `/photos/Urlaub-Kroatien-2026/`). Fotos in Event-Ordnern werden **nicht** automatisch verschoben, sondern bleiben dort
- **Fuer den Bilderrahmen macht es keinen Unterschied** — alle Fotos aus allen Unterordnern werden angezeigt

### settings.json (Standardwerte)

Erstelle die Datei `FamilyFrame/config/settings.json` mit folgendem Inhalt:

```json
{
  "slideshow_interval": 30,
  "transition": "fade",
  "transition_duration": 1.5,
  "order": "random",
  "show_overlay": true,
  "overlay_duration": 5,
  "night_mode": {
    "enabled": true,
    "dim_start": "22:00",
    "dim_end": "07:00",
    "brightness": 0.1
  },
  "sync_interval": 5
}
```

**Einstellungen erklaert:**

| Einstellung | Beschreibung | Werte |
|-------------|-------------|-------|
| `slideshow_interval` | Sekunden pro Foto | 10-300 |
| `transition` | Uebergangseffekt | `fade`, `slide`, `kenburns` |
| `transition_duration` | Uebergangsdauer in Sekunden | 0.5-3.0 |
| `order` | Reihenfolge der Fotos | `random`, `newest`, `chronological` |
| `show_overlay` | Bildunterschrift anzeigen | `true` / `false` |
| `overlay_duration` | Sekunden bis Einblendung verschwindet (0 = immer sichtbar) | 0-30 |
| `night_mode.enabled` | Nachtmodus aktiviert | `true` / `false` |
| `night_mode.dim_start` | Beginn der Abdunkelung | `"HH:MM"` |
| `night_mode.dim_end` | Ende der Abdunkelung | `"HH:MM"` |
| `night_mode.brightness` | Helligkeit im Nachtmodus (0=aus, 1=voll) | 0.0-1.0 |
| `sync_interval` | Sync-Intervall in Minuten | 1-60 |

> **Tipp**: Du kannst die Einstellungen jederzeit aendern, indem du die `settings.json` in OneDrive bearbeitest. Der Bilderrahmen uebernimmt die Aenderungen innerhalb von ~10 Minuten.

---

## 3. Foto-Ordner mit der Familie teilen

### Option A (Dediziertes Konto): Familie einladen

1. Oeffne OneDrive → Rechtsklick auf `/FamilyFrame/photos/` → **Teilen**
2. Waehle **Bestimmte Personen**
3. Aktiviere **Bearbeitung zulassen** (damit sie hochladen koennen)
4. Gib die E-Mail-Adressen aller Familienmitglieder ein
5. Klicke **Senden**

Jedes Familienmitglied erhaelt eine E-Mail mit einem Link. Der Ordner erscheint in deren OneDrive unter **Geteilt > Mit mir geteilt**.

### Option B (Geteilter Ordner): Ordner freigeben

Gleicher Ablauf — nur `/FamilyFrame/photos/` freigeben, NICHT den gesamten OneDrive.

### Wichtig: Nur den photos-Ordner teilen!

- Teile **nur** `/FamilyFrame/photos/`, nicht `/FamilyFrame/` und nicht `/FamilyFrame/config/`
- So kann die Familie Fotos hochladen, aber nicht die Einstellungen aendern
- Der `config/`-Ordner bleibt nur fuer den Admin zugaenglich

---

## 4. Familienmitglieder einrichten

Jedes Familienmitglied muss:

### Auf dem iPhone/Android:

1. **OneDrive App installieren** (kostenlos im App Store / Play Store)
2. Mit dem **eigenen Microsoft-Konto** anmelden (Hotmail, Outlook, M365 — egal welches)
3. Den geteilten Ordner oeffnen: **Geteilt** → **FamilyFrame photos**
4. Fotos hochladen: "+" Symbol → "Hochladen" → Fotos auswaehlen

### Alternativer Weg: Ueber den Webbrowser

1. Den Einladungslink aus der E-Mail oeffnen
2. Fotos per Drag & Drop in den Ordner ziehen

> Fuer eine einfachere Anleitung auf Deutsch, siehe: [family-guide-de.md](family-guide-de.md)

---

## 5. Fotos mit Beschreibung hochladen

### In der OneDrive App:
1. Foto hochladen
2. Auf das hochgeladene Foto tippen → **Details** (i-Symbol)
3. Im Feld **Beschreibung** die Bildunterschrift eingeben
4. Die App uebernimmt die Beschreibung als Caption auf dem Bilderrahmen

### Per E-Mail (Phase 2):
- **Betreff** → wird zur Bildunterschrift
- **E-Mail-Text** → wird zur Beschreibung
- **Anhang** → das Foto

### Per OneDrive Web:
1. Foto hochladen
2. Rechtsklick → **Details**
3. Beschreibung eingeben

---

## 6. Speicherplatz verwalten

### Bei 5 GB (dediziertes kostenloses Konto):

| Fotogroesse | Anzahl Fotos |
|-------------|-------------|
| ~2 MB (WhatsApp-Qualitaet) | ~2.500 |
| ~4 MB (Smartphone-Standard) | ~1.250 |
| ~8 MB (Smartphone-High-Quality) | ~625 |

Wenn der Speicher knapp wird:
- Aeltere Fotos loeschen (sie bleiben in der Cloudant-Datenbank als Metadaten)
- Oder: Microsoft 365 Basic (~2 EUR/Monat) fuer 100 GB

### Bei 1 TB (bestehendes M365-Konto):
Speicher ist kein Thema — selbst bei 10 Fotos pro Tag reicht es fuer Jahrzehnte.

---

## 7. Sicherheitshinweise

- **Freigabelinks**: Verwende "Bestimmte Personen", NICHT "Jeder mit dem Link"
- **Berechtigungen**: "Bearbeitung zulassen" nur fuer den `photos`-Ordner
- **Kein Zugriff auf Eltern-Ordner**: Wer Zugriff auf `photos` hat, sieht NICHT den uebergeordneten `FamilyFrame`-Ordner oder andere OneDrive-Inhalte
- **Familienmitglied entfernen**: OneDrive → Ordner → Teilen → Zugriff verwalten → Person entfernen
