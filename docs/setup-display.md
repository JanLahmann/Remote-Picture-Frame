# Display-Geraet einrichten

Anleitung fuer die Einrichtung des Bilderrahmens auf verschiedenen Geraeten.

---

## Option A: Android-Tablet (empfohlen)

### Empfohlene Hardware

| Modell | Display | Preis |
|--------|---------|-------|
| Samsung Galaxy Tab A9+ | 11" IPS, 1920x1200 | ~250 EUR |
| Lenovo Tab M11 | 11" IPS, 1920x1200 | ~200 EUR |
| Samsung Galaxy Tab A9 | 8.7" TFT, 1340x800 | ~150 EUR |

Dazu:
- Tablet-Staender mit Ladeoeffnung (~20-30 EUR) oder Wandhalterung (~30-40 EUR)
- USB-C Ladegeraet (meistens im Lieferumfang)

### Schritt 1: Tablet einrichten

1. Tablet einschalten, Sprache und WLAN einrichten
2. Google-Konto einrichten (wird fuer App-Installation benoetigt)
3. Alle System-Updates installieren (Einstellungen → Software-Update)

### Schritt 2: Fully Kiosk Browser installieren

**Fully Kiosk Browser** ist eine App, die das Tablet in einen dedizierten Bilderrahmen verwandelt. Einmalig ~7 EUR.

1. Google Play Store oeffnen
2. Suche: "Fully Kiosk Browser & Lockdown"
3. Installieren
4. App oeffnen → Lizenz kaufen (PLUS Lizenz, ~7 EUR)

### Schritt 3: Fully Kiosk Browser konfigurieren

App oeffnen → **Settings** (Zahnrad-Symbol):

**Web Content Settings:**
- Start URL: `https://deine-familyframe-url.example.com`
- Enable Fullscreen Mode: ON

**Web Auto Reload:**
- Auto Reload on Idle: OFF (die PWA synct selbst)
- Auto Reload on Internet Reconnect: ON
- Auto Reload After Page Error: ON, 60 seconds

**Device Management:**
- Keep Screen On: ON
- Screen Brightness: 80%
- Screensaver Timer: OFF (die PWA hat eigenen Nachtmodus)

**Kiosk Mode (KIOSK):**
- Enable Kiosk Mode: ON
- Kiosk Exit PIN: einen PIN setzen (z.B. 1234) — zum Verlassen des Kioskmodus
- Disable Status Bar: ON
- Disable Navigation Bar: ON
- Block Home Button: ON
- Block Back Button: ON
- Block Volume Buttons: OFF (damit Lautstaerke noch anpassbar)

**Remote Admin (REMOTE):**
- Enable Remote Admin: ON
- Remote Admin Password: ein sicheres Passwort setzen
- Remote Admin from Local Network: ON
- Remote Admin Port: 2323

> **Remote-Zugriff testen**: Oeffne im Browser auf deinem Laptop: 
> `http://<tablet-ip>:2323` — du siehst die Fully Kiosk Remote-Admin-Oberflaeche.

**Motion Detection (optional):**
- Enable Motion Detection: ON
- Turn Screen On on Motion: ON
- Screen Off Timer: 300 (Bildschirm nach 5 Minuten ohne Bewegung abdunkeln)

### Schritt 4: Auto-Start einrichten

In Fully Kiosk Browser → Settings → Other Settings:
- Launch on Boot: ON
- Restore Tab on Start: ON

Das Tablet startet jetzt bei jedem Neustart direkt in den Bilderrahmen-Modus.

### Schritt 5: TeamViewer installieren (fuer Fernwartung)

1. Play Store → "TeamViewer QuickSupport" installieren
2. App oeffnen → Notiere die **TeamViewer ID**
3. Auf deinem Computer: TeamViewer installieren → "Unbeaufsichtigter Zugriff" einrichten
4. Die Tablet-ID in deiner TeamViewer-Kontaktliste speichern

### Schritt 6: System-Einstellungen

In den Android-Einstellungen:

**Display:**
- Bildschirm-Timeout: 30 Minuten (als Fallback, Fully Kiosk uebernimmt)
- Adaptive Helligkeit: AUS (Fully Kiosk steuert die Helligkeit)

**Akku/Batterie:**
- Batterieschutz: ON / "Auf 85% begrenzen" (falls verfuegbar, schuetzt den Akku bei Dauerbetrieb)

**Netzwerk:**
- WLAN: Mit Omas WLAN verbinden
- "WLAN im Ruhemodus aktiviert lassen": IMMER

**Sicherheit:**
- Bildschirmsperre: keine (Fully Kiosk sperrt das Geraet)

### Schritt 7: Aufstellen

1. Tablet in den Staender setzen
2. USB-C Ladekabel anschliessen (Dauerbetrieb)
3. Kabel ordentlich verlegen
4. Fully Kiosk Browser starten → Kiosk-Modus aktivieren
5. Fertig! Die Fotos erscheinen automatisch.

---

## Option B: iPad

### Voraussetzungen
- iPad mit iOS 15 oder neuer
- Funktioniert mit jedem iPad-Modell

### Schritt 1: PWA installieren

1. Safari oeffnen
2. Die FamilyFrame-URL aufrufen: `https://deine-familyframe-url.example.com`
3. Teilen-Button (Quadrat mit Pfeil) → **Zum Home-Bildschirm**
4. Name: "FamilyFrame" → **Hinzufuegen**

### Schritt 2: Gefuehrten Zugriff einrichten (Guided Access)

Der Gefuehrte Zugriff sperrt das iPad auf eine einzelne App.

1. **Einstellungen** → **Bedienungshilfen** → **Gefuehrter Zugriff**
2. Gefuehrten Zugriff: ON
3. Code-Einstellungen: einen PIN festlegen (zum Beenden)
4. Display Auto-Sperre: Nie

### Schritt 3: Gefuehrten Zugriff starten

1. FamilyFrame-App vom Home-Bildschirm oeffnen
2. **Dreimal die Seitentaste / Home-Button druecken**
3. Optional: Bereiche auf dem Bildschirm deaktivieren (z.B. Ecken)
4. **Starten** tippen

Das iPad ist jetzt im Kiosk-Modus gesperrt. Zum Beenden: dreimal Seitentaste druecken + PIN eingeben.

### Schritt 4: Weitere Einstellungen

**Display & Helligkeit:**
- Automatische Sperre: Nie
- Auto-Helligkeit: AUS (manuell auf gewuenschte Helligkeit)

**Batterie:**
- Dauerhaft am Ladegeraet angeschlossen lassen

### Einschraenkungen gegenueber Android

| Feature | Android (Fully Kiosk) | iPad (Guided Access) |
|---------|----------------------|---------------------|
| Auto-Start nach Neustart | Ja | Nein (manuell App oeffnen + Guided Access starten) |
| Remote Admin (Web-Interface) | Ja | Nein |
| Bildschirm per Fernzugriff steuern | Ja (Fully Kiosk + TeamViewer) | Nur per TeamViewer |
| Bewegungserkennung | Ja | Nein |
| Kiosk-Modus-Qualitaet | Sehr gut | Gut |

---

## Option C: Raspberry Pi

Siehe die separate Anleitung: [`../raspberry-pi/README.md`](../raspberry-pi/README.md)

Kurzfassung:
```bash
git clone https://github.com/JanLahmann/Remote-Picture-Frame.git
cd Remote-Picture-Frame/raspberry-pi
sudo ./setup.sh https://deine-familyframe-url.example.com
sudo reboot
```

---

## Fehlerbehebung

### Alle Geraete

| Problem | Loesung |
|---------|---------|
| "Lade Fotos..." wird dauerhaft angezeigt | WLAN-Verbindung pruefen. Backend-URL korrekt? Browser-Konsole auf Fehler pruefen. |
| Fotos werden nicht aktualisiert | Sync laeuft alle 5 Min. Manuell: Seite neu laden. Pruefen ob Backend laeuft. |
| Bildschirm wird schwarz | Nachtmodus aktiv? `settings.json` pruefen. Android: Bildschirm-Timeout-Einstellungen. |
| Fotos werden abgeschnitten | Fotos werden in `object-fit: contain` angezeigt (mit schwarzen Balken). Falls Fotos fehlen: Cache leeren. |

### Android-spezifisch

| Problem | Loesung |
|---------|---------|
| Fully Kiosk zeigt weisse Seite | Cache leeren: Remote Admin → Clear Cache. Oder URL pruefen. |
| Tablet startet nicht in Kiosk | Fully Kiosk → Settings → Launch on Boot pruefen |
| Kann Kiosk-Modus nicht verlassen | Schnell 5x in die linke obere Ecke tippen → PIN eingeben |
| "App reagiert nicht" | Fully Kiosk startet automatisch neu. Falls nicht: TeamViewer. |

### iPad-spezifisch

| Problem | Loesung |
|---------|---------|
| Guided Access beendet sich | Dreimal Seitentaste druecken → neu starten |
| Bildschirm sperrt sich trotzdem | Einstellungen → Display → Auto-Sperre: Nie |
| Nach Neustart nicht im Kiosk | Manuell: App oeffnen → dreimal Seitentaste → Starten |
