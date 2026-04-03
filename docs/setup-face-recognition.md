# Gesichtserkennung einrichten (Azure Face API)

Die Gesichtserkennung identifiziert automatisch, wer auf den Fotos zu sehen ist.
Fotos werden in Personen-Ordner auf dem USB-Laufwerk sortiert, damit Oma auf ihrem
Fernseher nach Personen filtern kann.

**Optional:** Ohne Gesichtserkennung funktioniert alles andere normal — Fotos
werden einfach ohne Personen-Ordner angezeigt.

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

## 2. Raspberry Pi konfigurieren

Trage die Werte in die Konfigurationsdatei ein:

```bash
sudo nano /etc/familyframe/config.env
```

```
AZURE_FACE_KEY=dein-azure-face-schluessel
AZURE_FACE_ENDPOINT=https://familyframe-face.cognitiveservices.azure.com
```

---

## 3. Personen-Gruppe anlegen und trainieren

Die Personen-Gruppe muss einmalig ueber die Azure Face API eingerichtet werden.
Du kannst dies ueber die Admin-Oberflaeche (falls eingerichtet) oder per Skript tun.

### Per Kommandozeile auf dem Raspberry Pi:

```bash
cd /opt/familyframe
python3 -c "
from face_recognition import FaceRecognizer
import requests

ENDPOINT = 'https://familyframe-face.cognitiveservices.azure.com'
KEY = 'dein-schluessel'
GROUP_ID = 'familyframe-family'

headers = {'Ocp-Apim-Subscription-Key': KEY, 'Content-Type': 'application/json'}

# 1. Gruppe erstellen
r = requests.put(f'{ENDPOINT}/face/v1.0/persongroups/{GROUP_ID}',
    headers=headers,
    json={'name': 'FamilyFrame Familie', 'recognitionModel': 'recognition_04'})
print(f'Gruppe erstellen: {r.status_code}')

# 2. Person hinzufuegen (fuer jedes Familienmitglied wiederholen)
r = requests.post(f'{ENDPOINT}/face/v1.0/persongroups/{GROUP_ID}/persons',
    headers=headers, json={'name': 'Anna'})
print(f'Anna hinzugefuegt: {r.json()}')
person_id = r.json()['personId']

# 3. Beispielbilder hinzufuegen (3-6 pro Person)
with open('anna_foto1.jpg', 'rb') as f:
    r = requests.post(
        f'{ENDPOINT}/face/v1.0/persongroups/{GROUP_ID}/persons/{person_id}/persistedFaces?detectionModel=detection_03',
        headers={'Ocp-Apim-Subscription-Key': KEY, 'Content-Type': 'application/octet-stream'},
        data=f.read())
    print(f'Gesicht hinzugefuegt: {r.status_code}')

# 4. Trainieren (nach allen Personen und Bildern)
r = requests.post(f'{ENDPOINT}/face/v1.0/persongroups/{GROUP_ID}/train', headers=headers)
print(f'Training gestartet: {r.status_code}')
"
```

### Tipps fuer gute Beispielbilder:

- **3-6 Fotos pro Person** fuer gute Erkennung
- Verschiedene Winkel (frontal, leicht seitlich)
- Verschiedene Beleuchtungen
- Mit und ohne Brille
- Aktuelle Fotos (nicht 10 Jahre alt)

---

## 4. Testen

Starte einen manuellen Sync:

```bash
sudo systemctl start familyframe-sync
```

Pruefe die Logs:

```bash
cat /var/log/familyframe/sync.log
```

Du solltest Zeilen wie diese sehen:

```
2026-04-03 14:30:15 [INFO] Recognized in strand_2026.jpg: Anna, Thomas
```

Auf dem USB-Laufwerk sollten Personen-Ordner erscheinen:

```bash
ls /opt/familyframe/mnt/
# Alle Fotos/  Anna/  Thomas/  Maria/
```

---

## 5. Ergebnis auf dem Fernseher

Oma sieht auf ihrem Samsung TV:

```
FAMILYFRAME (USB)
├── Alle Fotos          ← alle Fotos
├── Anna                ← Fotos mit Anna
├── Thomas              ← Fotos mit Thomas
├── Maria               ← Fotos mit Maria
```

Sie navigiert mit der Fernbedienung in den gewuenschten Ordner.

---

## 6. Kosten

- **Azure Face F0 (Free)**: 30.000 Transaktionen/Monat
- Pro Foto werden ~2-3 Transaktionen benoetigt (Detect + Identify + ggf. List Persons)
- Das reicht fuer ~10.000 Fotos/Monat — weit mehr als noetig
- **Kosten: 0 EUR/Monat**

---

## 7. Hinweise

- **Datenschutz**: Die Fotos werden an Azure zur Verarbeitung geschickt. Die Gesichtsdaten werden nur in deiner Azure-Ressource gespeichert und nicht mit anderen geteilt.
- **Genauigkeit**: Mit 3-6 guten Beispielbildern pro Person liegt die Erkennungsrate bei ~95%+.
- **Neue Familienmitglieder**: Zur Personen-Gruppe hinzufuegen, Beispielbilder hochladen, neu trainieren.
- **Wenn die Erkennung nicht funktioniert**: Mehr Beispielbilder hinzufuegen und neu trainieren.
- **Ohne Azure-Konfiguration**: Die Gesichtserkennung wird einfach uebersprungen. Fotos landen nur in "Alle Fotos" und ggf. Event-Ordnern.
