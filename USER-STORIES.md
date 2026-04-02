# FamilyFrame - User Stories (Omas Perspektive)

Grandma hat 3 Kinder und 6 Enkel. Alle laden regelmaessig Fotos hoch — taeglich bis woechentlich, plus Urlaub, Feiertage, besondere Anlaesse. Der Bilderrahmen ist ihr Fenster zur Familie.

---

## Prinzip: Zero-Effort by Default, Optional Interaction

Oma muss **nie** etwas tun. Der Rahmen funktioniert einfach. Aber **wenn** sie moechte, kann sie intuitiv interagieren — ohne Angst, etwas kaputt zu machen.

---

## 1. Zero-Interaction Stories (Der Rahmen funktioniert einfach)

### US-1.1: Morgens einschalten
**Als** Oma  
**moechte ich**, dass der Bilderrahmen morgens automatisch hell wird und Fotos zeigt,  
**damit** ich beim Fruehstueck meine Familie sehe.

**Akzeptanzkriterien:**
- Bildschirm hellt sich automatisch zum konfigurierten Zeitpunkt auf (z.B. 7:00)
- Slideshow laeuft sofort — kein Startbildschirm, kein Laden, keine Interaktion
- Zeigt sofort ein Foto, nicht einen schwarzen/weissen Bildschirm

### US-1.2: Neue Fotos bemerken
**Als** Oma  
**moechte ich** merken, wenn neue Fotos angekommen sind,  
**damit** ich mich darauf freue und sie bewusst anschaue.

**Akzeptanzkriterien:**
- Neue Fotos werden bevorzugt angezeigt (hoehere Wahrscheinlichkeit in der Rotation)
- Optional: Kurze, dezente Einblendung "3 neue Fotos von Maria" beim ersten Anzeigen
- Kein Piepen, kein Aufblinken — sanft und unaufdringlich

### US-1.3: Abends abdunkeln
**Als** Oma  
**moechte ich**, dass der Bildschirm abends automatisch dunkler wird,  
**damit** er mich nicht beim Schlafen stoert.

**Akzeptanzkriterien:**
- Bildschirm dimmt sanft zum konfigurierten Zeitpunkt (z.B. 22:00)
- Minimale Helligkeit einstellbar (z.B. 10% oder komplett aus)
- Morgens wieder automatisch hell

### US-1.4: Nach Stromausfall
**Als** Oma  
**moechte ich**, dass der Bilderrahmen nach einem Stromausfall von alleine wieder startet,  
**damit** ich nichts tun muss.

**Akzeptanzkriterien:**
- Tablet startet automatisch und oeffnet die Slideshow
- Zeigt gecachte Fotos auch ohne Internet
- Synct automatisch, sobald WLAN wieder verfuegbar

### US-1.5: Keine Wiederholungen
**Als** Oma  
**moechte ich** nicht immer die gleichen 5 Fotos sehen,  
**damit** es sich frisch und abwechslungsreich anfuehlt.

**Akzeptanzkriterien:**
- Algorithmus vermeidet kurzfristige Wiederholungen (kein Foto innerhalb von X Zyklen nochmal)
- Alle Fotos kommen dran, nicht nur die neuesten
- Balance zwischen neuen und alten Fotos (z.B. 70% neuere, 30% aeltere)

---

## 2. Optionale Interaktions-Stories (Wenn Oma moechte)

### US-2.1: Bei einem Foto verweilen
**Als** Oma  
**moechte ich** die Slideshow anhalten koennen, wenn mir ein Foto besonders gefaellt,  
**damit** ich es in Ruhe anschauen kann.

**Akzeptanzkriterien:**
- Einfacher Tipp irgendwo auf den Bildschirm pausiert die Slideshow
- Deutliches aber dezentes Zeichen, dass pausiert ist (z.B. kleines Pause-Symbol)
- Nach 5 Minuten Pause: automatisch weiter (falls Oma vergisst)
- Erneuter Tipp: weiter

### US-2.2: Foto ueberspringen
**Als** Oma  
**moechte ich** ein Foto ueberspringen koennen,  
**damit** ich zum naechsten komme.

**Akzeptanzkriterien:**
- Wisch nach links/rechts: naechstes/vorheriges Foto
- Oder: Tipp auf rechte/linke Bildhaelfte
- Uebergang ist sanft, nicht abrupt

### US-2.3: Wer hat das geschickt?
**Als** Oma  
**moechte ich** sehen koennen, wer ein Foto geschickt hat und wann es aufgenommen wurde,  
**damit** ich die Geschichte hinter dem Foto kenne.

**Akzeptanzkriterien:**
- Bildunterschrift zeigt: Caption, Absender, Datum, Ort
- Einblendung verschwindet nach ein paar Sekunden
- Kann durch Tipp in die Mitte wieder eingeblendet werden

### US-2.4: Foto einem Besucher zeigen
**Als** Oma  
**moechte ich** ein bestimmtes Foto wiederfinden und meiner Freundin Helga zeigen koennen,  
**damit** ich stolz meine Familie praesentieren kann.

**Akzeptanzkriterien:**
- Wisch nach oben: Mini-Galerie / Uebersicht der letzten Fotos (Thumbnail-Leiste)
- Oma tippt auf ein Thumbnail → Foto wird gross angezeigt
- Zurueck zur Slideshow: einfacher Tipp oder automatisch nach 30s

### US-2.5: Nur Fotos von einem Enkel sehen
**Als** Oma  
**moechte ich** manchmal nur Fotos von einem bestimmten Enkel sehen,  
**damit** ich z.B. sehe, wie schnell die kleine Emma waechst.

**Akzeptanzkriterien:**
- In der Mini-Galerie: Filter nach Person (z.B. "Emmas Fotos")
- Slideshow zeigt dann nur Fotos dieser Person
- Automatischer Reset nach 30 Minuten (zurueck zu allen Fotos)

### US-2.6: Lieblingsfoto markieren
**Als** Oma  
**moechte ich** ein Foto als Favorit markieren koennen,  
**damit** es oefter gezeigt wird.

**Akzeptanzkriterien:**
- Langer Druck auf ein Foto → Herz-Symbol erscheint → Foto ist Favorit
- Favoriten werden haeufiger in der Rotation gezeigt
- Favoriten koennen auch als eigene Slideshow abgespielt werden

---

## 3. Emotionale / Kontextuelle Stories

### US-3.1: Geburtstags-Highlights
**Als** Oma  
**moechte ich** an Geburtstagen meiner Kinder und Enkel besondere Fotos sehen,  
**damit** sich der Tag besonders anfuehlt.

**Akzeptanzkriterien:**
- Am Geburtstag eines Familienmitglieds: Fotos dieser Person werden bevorzugt gezeigt
- Optional: Spezielle Einblendung "Alles Gute zum Geburtstag, Emma!"
- Admin kann Geburtstage in einer Konfiguration hinterlegen

### US-3.2: "An diesem Tag" — Erinnerungen
**Als** Oma  
**moechte ich** manchmal Fotos von vor einem Jahr (oder laenger) sehen,  
**damit** ich mich an schoene Momente erinnere.

**Akzeptanzkriterien:**
- Einmal pro Tag: ein "An diesem Tag vor X Jahren"-Foto einstreuen
- Einblendung: "Vor 1 Jahr — Urlaub in Italien"
- Nur wenn ein passendes Foto existiert (gleicher Monat+Tag, anderes Jahr)

### US-3.3: Urlaubsserie als Geschichte
**Als** Oma  
**moechte ich**, dass Urlaubsfotos zusammenhaengend gezeigt werden,  
**damit** ich die Reise als Geschichte erlebe.

**Akzeptanzkriterien:**
- Fotos vom gleichen Tag/Ort werden in einer Sequenz gezeigt (nicht einzeln verstreut)
- Caption zeigt den Kontext: "Marias Urlaub in Griechenland, Juli 2026"
- Nach der Serie: zurueck zur normalen Rotation

### US-3.4: Vermissungs-Indikator
**Als** Oma (oder als Admin)  
**moechte ich** bemerken, wenn ein Kind/Enkel laengere Zeit keine Fotos geschickt hat,  
**damit** ich (oder der Admin) nachfragen kann.

**Akzeptanzkriterien:**
- Admin-Dashboard zeigt: "Letztes Foto von Thomas: vor 23 Tagen"
- Optional auf dem Rahmen: dezenter Hinweis (z.B. im Overlay ab und zu)
- Kein Schuldzuweisung-Charakter — eher liebevoll

### US-3.5: Erste Fotos besonders wuerdigen
**Als** Oma  
**moechte ich**, dass die allerersten Fotos (z.B. eines neuen Enkels) besonders gezeigt werden,  
**damit** sich der Moment besonders anfuehlt.

**Akzeptanzkriterien:**
- Erste Fotos eines neuen Uploaders: laenger angezeigt, groesser, mit besonderer Einblendung
- Admin kann ein Foto als "Highlight" markieren → wird oefter und prominenter gezeigt

---

## 4. Schutz-Stories (Nichts geht kaputt)

### US-4.1: Versehentliche Beruehrung
**Als** Oma  
**moechte ich**, dass nichts Schlimmes passiert, wenn ich aus Versehen den Bildschirm beruehre,  
**damit** ich keine Angst vor dem Geraet habe.

**Akzeptanzkriterien:**
- Ein einzelner Tipp pausiert nur kurz (und geht von allein weiter)
- Kein Tipp/Geste kann die App verlassen, Einstellungen aendern oder loeschen
- Kein "Sind Sie sicher?"-Dialog, keine verwirrenden Menues
- Schlimmster Fall: Slideshow pausiert und geht nach 5 Minuten weiter

### US-4.2: Einfach ignorieren koennen
**Als** Oma  
**moechte ich** den Bilderrahmen einfach ignorieren koennen, wenn ich keine Lust habe,  
**damit** er mich nie stoert.

**Akzeptanzkriterien:**
- Keine Sounds, keine Benachrichtigungen, keine blinkenden Elemente
- Bildschirm im Nachtmodus nahezu unsichtbar
- Kein Druck, etwas zu tun oder zu bestaetigen

---

## 5. Mapping: Stories → Features → Status

| Story | Feature | Status |
|-------|---------|--------|
| US-1.1 Morgens einschalten | Nachtmodus-Zeitplan + Auto-Start | Implementiert |
| US-1.2 Neue Fotos bemerken | Smart Rotation + "Neu"-Badge | **Neu: Smart Rotation** |
| US-1.3 Abends abdunkeln | Nachtmodus | Implementiert |
| US-1.4 Nach Stromausfall | Kiosk Auto-Start + Service Worker Cache | Implementiert |
| US-1.5 Keine Wiederholungen | Weighted Random (nicht reines random) | **Neu: Smart Rotation** |
| US-2.1 Verweilen | Tap to pause + Auto-Resume | Teilweise (kein Auto-Resume) |
| US-2.2 Ueberspringen | Swipe/Tap Navigation | Implementiert |
| US-2.3 Wer hat das geschickt? | Photo Overlay | Implementiert |
| US-2.4 Besucher zeigen | Mini-Galerie / Thumbnail-Leiste | **Neu** |
| US-2.5 Nach Person filtern | Person-Filter im Display | **Neu** |
| US-2.6 Favorit markieren | Favorites-System | **Neu** |
| US-3.1 Geburtstags-Highlights | Geburtstags-Konfiguration | **Neu** |
| US-3.2 "An diesem Tag" | On-This-Day-Feature | **Neu** |
| US-3.3 Urlaubsserie | Sequenz-Erkennung (Datum+Ort) | **Neu** |
| US-3.4 Vermissungs-Indikator | Admin-Dashboard: Letzte-Aktivitaet-Anzeige | **Neu (Admin)** |
| US-3.5 Erste Fotos wuerdigen | Highlight-System | **Neu** |
| US-4.1 Versehentliche Beruehrung | Safe Touch (keine gefaehrlichen Gesten) | Implementiert |
| US-4.2 Einfach ignorieren | Keine Sounds/Notifications | Implementiert |

---

## 6. Priorisierte neue Features (aus User Stories abgeleitet)

### Prioritaet 1 — Sofort umsetzen (verbessert Kernfunktion)

1. **Smart Rotation** (US-1.2, US-1.5)
   - Weighted Random: neuere Fotos haeufiger, aber alle kommen dran
   - Wiederholungs-Vermeidung: Foto nicht innerhalb der letzten N Zyklen nochmal
   - Neue Fotos bevorzugt zeigen (erste 24h nach Upload: hoehere Gewichtung)

2. **Auto-Resume nach Pause** (US-2.1)
   - Nach 5 Minuten Pause automatisch weiterlaufen
   - Countdown-Anzeige im Pause-Modus (optional)

3. **"Neu"-Indikator** (US-1.2)
   - Dezentes "Neu"-Badge im Overlay fuer Fotos der letzten 24h
   - Oder: kleine Zahl "3 neue Fotos" einmalig einblenden

### Prioritaet 2 — Naechste Iteration (emotionale Features)

4. **"An diesem Tag" / Erinnerungen** (US-3.2)
   - Fotos vom gleichen Kalendertag aus frueheren Jahren einstreuen
   - Overlay: "Vor 1 Jahr"

5. **Favoriten-System** (US-2.6)
   - Langer Druck → Herz → Favorit
   - Favoriten hoeher gewichtet in Rotation
   - Admin kann auch Favoriten setzen

6. **Vermissungs-Indikator im Admin-Dashboard** (US-3.4)
   - "Letztes Foto von [Name]: vor X Tagen" pro Familienmitglied

### Prioritaet 3 — Spaeter (erweiterte Interaktion)

7. **Mini-Galerie** (US-2.4)
   - Wisch nach oben: Thumbnail-Leiste am unteren Rand
   - Scrollen und tippen zum Auswaehlen

8. **Person-Filter** (US-2.5)
   - In der Mini-Galerie: Filterbuttons pro Person
   - Slideshow nur mit Fotos einer Person
   - Auto-Reset nach 30 Minuten

9. **Geburtstags-Modus** (US-3.1)
   - Konfigurierbare Geburtstags-Liste
   - An dem Tag: Fotos der Person bevorzugt + optionale Einblendung

10. **Foto-Serien / Urlaubsmodus** (US-3.3)
    - Clustering nach Datum+Ort
    - Zusammenhaengend anzeigen mit Kontext-Caption
