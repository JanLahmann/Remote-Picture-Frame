# Gesichtserkennung einrichten (Azure Face API)

Die Gesichtserkennung identifiziert automatisch, wer auf den Fotos zu sehen ist.
Oma kann dann auf dem Bilderrahmen nach Personen filtern.

---

## 1. Azure Face Resource erstellen (kostenlos)

1. Gehe zu https://portal.azure.com
2. Suche nach **"Face"** → **Face** → **Erstellen**
3. Einstellungen:
   - **Abonnement**: Dein Azure-Abonnement (kostenloses Konto reicht)
   - **Ressourcengruppe**: Neue erstellen, z.B. `familyframe-rg`
   - **Region**: `West Europe` (oder naechstgelegene)
   - **Name**: z.B. `familyframe-face`
   - **Tarif**: **Free F0** (30.000 Transaktionen/Monat — mehr als genug)
4. **Erstellen** klicken

### Schluessel und Endpunkt kopieren

Nach der Erstellung:
1. Gehe zur Face-Ressource → **Schluessel und Endpunkt**
2. Kopiere:
   - **Schluessel 1** → wird `AZURE_FACE_KEY`
   - **Endpunkt** → wird `AZURE_FACE_ENDPOINT` (z.B. `https://familyframe-face.cognitiveservices.azure.com`)

---

## 2. Backend konfigurieren

Fuege die folgenden Werte zu `local.settings.json` (fuer lokale Entwicklung) und zur IBM Cloud Function-Konfiguration hinzu:

```json
{
  "AZURE_FACE_ENDPOINT": "https://familyframe-face.cognitiveservices.azure.com",
  "AZURE_FACE_KEY": "dein-azure-face-schluessel"
}
```

Fuer IBM Cloud Functions:
```bash
ibmcloud fn package update familyframe \
  -p AZURE_FACE_ENDPOINT "https://familyframe-face.cognitiveservices.azure.com" \
  -p AZURE_FACE_KEY "dein-schluessel"
```

---

## 3. Personen anlegen und trainieren (Admin-Oberflaeche)

1. Starte die Admin-Oberflaeche (`npm run dev` im `admin-web/` Ordner)
2. Gehe zum Tab **"Gesichter"**
3. Klicke **"Gesichtserkennung einrichten"** (erstellt die Person Group bei Azure)
4. Fuer jedes Familienmitglied:
   - Name eingeben → **"Hinzufuegen"**
   - **"+ Foto"** klicken → 3-6 verschiedene Fotos mit dem Gesicht der Person hochladen
   - Tipps fuer gute Beispielbilder:
     - Verschiedene Winkel (frontal, leicht seitlich)
     - Verschiedene Beleuchtungen
     - Mit und ohne Brille
     - Aktuell (nicht 10 Jahre alt)
5. Klicke **"Modell trainieren"**
6. Warte bis der Status **"Aktiv"** zeigt

---

## 4. Testen

Lade ein neues Foto hoch (WhatsApp, Web-Upload oder OneDrive). In den Foto-Metadaten (Admin → Fotos → Foto anklicken) sollte das Feld `people` die erkannten Namen enthalten.

Auf dem Bilderrahmen:
- Das Overlay zeigt die erkannten Personen unter dem Foto
- Doppeltippen zeigt die Personenfilter-Buttons mit den erkannten Namen

---

## 5. Kosten

- **Azure Face F0 (Free)**: 30.000 Transaktionen/Monat
- Pro Foto werden ~2-3 Transaktionen benoetigt (Detect + Identify + ggf. List Persons)
- Das reicht fuer ~10.000 Fotos/Monat — weit mehr als noetig

---

## 6. Hinweise

- **Datenschutz**: Die Fotos werden an Azure zur Verarbeitung geschickt. Die Gesichtsdaten werden nur in deiner Azure-Ressource gespeichert und nicht mit anderen geteilt.
- **Genauigkeit**: Mit 3-6 guten Beispielbildern pro Person liegt die Erkennungsrate bei ~95%+.
- **Neue Familienmitglieder**: Einfach in der Admin-Oberflaeche hinzufuegen, Beispielbilder hochladen, neu trainieren.
- **Wenn die Erkennung nicht funktioniert**: Mehr Beispielbilder hinzufuegen und neu trainieren.
- **Ohne Azure-Konfiguration**: Die Gesichtserkennung wird einfach uebersprungen. Fotos werden trotzdem normal verarbeitet.
