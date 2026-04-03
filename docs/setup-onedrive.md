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

### Option B: Geteilter Ordner im bestehenden OneDrive

Einen Unterordner im bestehenden Family-OneDrive freigeben.

**Vorteile:**
- Kein zusaetzliches Konto
- Nutzt den bestehenden 1 TB Speicher

**Einrichtung:**
1. Melde dich bei https://onedrive.live.com mit deinem M365-Konto an
2. Erstelle den Ordner `/FamilyFrame/photos/`

---

## 2. Ordnerstruktur erstellen

```
FamilyFrame/
  photos/                          ← Upload-Ordner (alle laden hier hoch)
    Urlaub-Kroatien-2026/          ← optional: Familie kann Event-Ordner erstellen
    Weihnachten-2027/              ← optional: weitere Event-Ordner
```

### Wie funktioniert das?

- **Upload**: Alle Familienmitglieder laden Fotos direkt in `/FamilyFrame/photos/` hoch
- **Event-Ordner**: Familienmitglieder koennen optional eigene Unterordner erstellen (z.B. `/photos/Urlaub-Kroatien-2026/`). Diese Ordner erscheinen als eigene Ordner auf Omas Fernseher
- **Personen-Ordner**: Der Raspberry Pi erstellt automatisch Ordner fuer erkannte Personen (z.B. `/Anna/`, `/Thomas/`) auf dem USB-Laufwerk — diese entstehen NICHT in OneDrive, sondern nur lokal auf dem RPi
- **Fuer Oma macht es keinen Unterschied** — sie sieht alle Fotos aus allen Ordnern

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

- Teile **nur** `/FamilyFrame/photos/`, nicht den gesamten OneDrive
- So kann die Familie nur Fotos hochladen und sieht keine anderen Dateien

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

## 5. Fotos hochladen

### In der OneDrive App:
1. Gehe zu **Geteilt** → **FamilyFrame photos**
2. Tippe auf **+** → **Hochladen** → **Fotos und Videos**
3. Waehle die Fotos aus → **Fertig**

### Per OneDrive Web (Browser):
1. Oeffne den Einladungslink im Browser
2. Ziehe Fotos per **Drag & Drop** in den Ordner
3. Oder klicke auf **Hochladen** → Fotos auswaehlen

### Event-Ordner:
Familienmitglieder koennen eigene Ordner fuer Anlaesse erstellen (z.B. "Weihnachten 2027"). Einfach in OneDrive einen neuen Unterordner anlegen und die Fotos dort hochladen. Der Ordner erscheint automatisch auf Omas Fernseher.

> **Hinweis**: Bildunterschriften werden im aktuellen Setup (Samsung TV USB-Mediaplayer) nicht angezeigt. Der Fernseher zeigt nur die Fotos selbst. Bildunterschriften koennen in einem spaeteren Update direkt in die Fotos eingebrannt werden (Path B).

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
