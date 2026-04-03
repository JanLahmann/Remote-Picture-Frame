# FamilyFrame - Anleitung fuer die Familie

**So laedt ihr Fotos auf Omas digitalen Bilderrahmen hoch.**

Omas Fernseher zeigt automatisch alle Fotos an, die ihr hochladet. Einfach ein Foto in den geteilten OneDrive-Ordner laden — fertig! Die Fotos erscheinen innerhalb weniger Minuten auf dem Fernseher.

---

## So funktioniert es

1. Ihr ladet Fotos in einen **geteilten OneDrive-Ordner** hoch
2. Ein kleiner Computer (Raspberry Pi) an Omas Fernseher laedt die Fotos automatisch herunter
3. Oma sieht die Fotos auf ihrem Fernseher — ueber den **USB-Mediaplayer**, den sie schon kennt
4. Fotos werden automatisch nach **Personen** sortiert (Gesichtserkennung)

---

## Weg 1: OneDrive-App (empfohlen)

### Einmalige Einrichtung (5 Minuten)

1. **OneDrive App installieren** (falls noch nicht vorhanden)
   - iPhone: Im App Store nach "OneDrive" suchen
   - Android: Im Google Play Store nach "OneDrive" suchen

2. **Anmelden** mit deinem Microsoft-Konto (Hotmail, Outlook, oder beliebig)

3. **Einladung annehmen**
   - Du hast eine E-Mail mit einer Einladung zum geteilten Ordner bekommen
   - Klicke auf den Link in der E-Mail
   - Der Ordner "FamilyFrame photos" erscheint unter **Geteilt**

### Fotos hochladen

1. Oeffne die **OneDrive App**
2. Gehe zu **Geteilt** → **FamilyFrame photos**
3. Tippe auf **+** → **Hochladen** → **Fotos und Videos**
4. Waehle die Fotos aus → **Fertig**

> **Tipps**:
> - Du kannst **mehrere Fotos auf einmal** hochladen
> - **Querformat** sieht auf dem Fernseher besser aus als Hochformat
> - Fotos erscheinen innerhalb von ~5 Minuten auf Omas Fernseher

---

## Weg 2: Web-Upload (kein Microsoft-Konto noetig)

Fuer alle, die kein OneDrive nutzen moechten:

1. Oeffne **[Upload-Link]** im Browser (Handy, Tablet, oder Laptop)
2. Gib den **Familien-PIN** ein (bekommst du vom Admin)
3. Waehle einen **Ordner** aus (z.B. "Weihnachten 2027") oder lade in "Allgemein" hoch
4. Waehle **Fotos** aus oder ziehe sie per Drag & Drop ins Fenster
5. Optional: Schreibe eine **Bildunterschrift** und waehle deinen **Namen** aus
6. Tippe auf **Hochladen**

> **Tipp**: Du kannst auch neue Ordner direkt auf der Upload-Seite erstellen.

---

## Weg 3: Ueber den OneDrive-Webbrowser (kein App noetig)

1. Oeffne den **Einladungslink** aus der E-Mail im Browser
2. Ziehe Fotos per **Drag & Drop** in den Ordner
3. Oder klicke auf **Hochladen** → Fotos auswaehlen

> Das funktioniert auf jedem Geraet mit Browser — Handy, Tablet, Laptop.

---

## Event-Ordner erstellen

Ihr koennt **eigene Ordner** fuer besondere Anlaesse erstellen:

1. Oeffne den geteilten Ordner in OneDrive
2. Erstelle einen neuen Ordner, z.B. **"Weihnachten 2027"** oder **"Urlaub Kroatien"**
3. Lade die Fotos in diesen Ordner hoch

Oma sieht den Ordner auf ihrem Fernseher und kann ihn mit der Fernbedienung oeffnen.

---

## Was Oma auf dem Fernseher sieht

Oma oeffnet wie gewohnt den **USB-Mediaplayer** auf ihrem Panasonic-Fernseher. Sie sieht folgende Ordner:

```
FAMILYFRAME (USB)
├── Alle Fotos          ← alle Fotos von allen
├── Anna                ← nur Fotos mit Anna
├── Thomas              ← nur Fotos mit Thomas
├── Maria               ← nur Fotos mit Maria
├── Weihnachten 2027    ← euer Event-Ordner
```

- **Alle Fotos**: Zeigt alle Fotos als Diashow
- **Personen-Ordner** (Anna, Thomas, ...): Automatisch erstellt durch Gesichtserkennung
- **Event-Ordner**: Von euch in OneDrive erstellt

Oma navigiert mit ihrer **normalen Fernbedienung** — sie muss nichts Neues lernen!

---

## Tipps

- **Querformat** sieht auf dem Fernseher besser aus als Hochformat
- **Jederzeit hochladen**: Es gibt keinen falschen Zeitpunkt. Oma sieht neue Fotos automatisch
- **Event-Ordner** helfen Oma, bestimmte Anlaesse wiederzufinden
- **Kein WLAN?** Kein Problem — alle bereits heruntergeladenen Fotos bleiben auf dem Fernseher

---

## Haeufige Fragen

**Wie schnell sieht Oma meine Fotos?**
Innerhalb von ~5 Minuten. Der Raspberry Pi prueft alle 5 Minuten auf neue Fotos.

**Sieht die Familie meine anderen OneDrive-Dateien?**
Nein. Ihr seht nur den geteilten Foto-Ordner. Nichts anderes.

**Kann ich Fotos wieder loeschen?**
Ja. Loesche das Foto einfach aus dem geteilten OneDrive-Ordner. Beim naechsten Sync wird es auch vom Fernseher entfernt.

**Wie viele Fotos kann ich hochladen?**
Sehr viele! Der Speicher reicht fuer tausende Fotos.

**Muss Oma etwas tun?**
Nein! Oma oeffnet einfach den USB-Mediaplayer wie immer. Neue Fotos erscheinen automatisch.

**Was passiert wenn Omas WLAN ausfaellt?**
Alle bereits heruntergeladenen Fotos bleiben verfuegbar. Neue Fotos erscheinen, sobald das WLAN wieder da ist.

**Kann Oma Fotos von einer bestimmten Person sehen?**
Ja! Oma oeffnet einfach den Ordner mit dem Namen der Person (z.B. "Anna"). Die Gesichtserkennung sortiert automatisch.

**Woher weiss der Bilderrahmen, wer auf dem Foto ist?**
Eine Gesichtserkennung (Azure Face API) identifiziert automatisch die Personen. Der Admin hat vorher Beispielfotos von jedem Familienmitglied hochgeladen.

---

## Hilfe

Wenn etwas nicht klappt, meldet euch bei **[Name des Admins]**.
