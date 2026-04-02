# E-Mail-Upload mit Power Automate einrichten

Diese Anleitung beschreibt, wie man eine E-Mail-Adresse einrichtet, an die Familienmitglieder Fotos schicken koennen. Die Fotos werden automatisch in OneDrive gespeichert.

**Power Automate ist in Microsoft 365 enthalten — keine zusaetzlichen Kosten.**

---

## 1. Gemeinsames Postfach erstellen

### Option A: Ueber Microsoft 365 Admin Center

1. Gehe zu https://admin.microsoft.com
2. **Gruppen** → **Freigegebene Postfaecher** → **Freigegebenes Postfach hinzufuegen**
3. Name: `FamilyFrame Fotos`
4. E-Mail: `bilderrahmen@deine-domain.de`
5. Mitglieder hinzufuegen: dein Admin-Konto (damit du den Posteingang sehen kannst)

### Option B: Alias auf bestehendem Konto

Falls du keine eigene Domain hast oder das dedizierte FamilyFrame-Outlook-Konto verwendest:
- Das Konto `familyframe.mustermann@outlook.com` direkt als Ziel verwenden
- Die Familie schickt Fotos einfach an diese Adresse

---

## 2. Power Automate Flow erstellen

1. Gehe zu https://make.powerautomate.com
2. Melde dich mit deinem M365-Konto an
3. Klicke **Erstellen** → **Automatisierter Cloud-Flow**

### Flow-Name
`FamilyFrame - E-Mail zu OneDrive`

### Trigger

1. Suche: **"Wenn eine neue E-Mail eintrifft"** (Office 365 Outlook)
2. Konfiguriere:
   - **Ordner**: Posteingang
   - **Nur mit Anlage**: Ja
   - **Anlageneinbeziehen**: Ja
   - Falls gemeinsames Postfach: **Postfach-Adresse**: `bilderrahmen@deine-domain.de`

### Aktionen

**Aktion 1: "Auf alle anwenden"** (Apply to each)
- Eingabe: `Anlagen` (vom Trigger)

Innerhalb der Schleife:

**Aktion 1a: Bedingung**
- Pruefen ob die Anlage ein Bild ist:
  - `Anlagenname` **endet mit** `.jpg` ODER `.jpeg` ODER `.png` ODER `.heic`
  - ODER: `Anlageinhaltstyp` **beginnt mit** `image/`

**Aktion 1b (Wenn ja): "Datei erstellen"** (OneDrive for Business oder OneDrive)
- **Ordnerpfad**: `/FamilyFrame/photos`
- **Dateiname**: `@{triggerOutputs()?['body/from']}__@{utcNow('yyyyMMdd_HHmmss')}__@{items('Apply_to_each')?['name']}`
  - Das fuegt den Absender und Zeitstempel zum Dateinamen hinzu
  - Beispiel: `maria@gmail.com__20260715_180000__strand.jpg`
- **Dateiinhalt**: `Anlageinhalt` (aus der Schleife)

> **Hinweis zum Dateinamen**: Der Absendername im Dateinamen hilft dem Backend, 
> das Feld `uploaded_by` automatisch zu setzen. Das Backend parst den Dateinamen 
> und extrahiert den Absender.

### Fertig

Klicke **Speichern**. Der Flow ist jetzt aktiv.

---

## 3. Flow testen

1. Schicke eine E-Mail mit einem Foto-Anhang an die Bilderrahmen-Adresse
2. Warte 1-2 Minuten
3. Pruefe in OneDrive → `/FamilyFrame/photos/` ob das Foto angekommen ist
4. Pruefe in Power Automate → **Meine Flows** → Flow oeffnen → **Ausfuehrungsverlauf**

### Haeufige Probleme beim Testen

| Problem | Loesung |
|---------|---------|
| Flow wird nicht ausgeloest | Pruefe ob die E-Mail im richtigen Postfach ankommt. Trigger-Bedingungen pruefen. |
| "Autorisierung fehlgeschlagen" | Power Automate → Verbindungen → OneDrive-Verbindung erneuern |
| Datei wird nicht in OneDrive gespeichert | Ordnerpfad pruefen. Existiert `/FamilyFrame/photos/`? |
| Nur manche Bilder werden gespeichert | Dateitypfilter pruefen. HEIC-Format hinzufuegen falls iPhones verwendet werden. |

---

## 4. (Optional) Bestaetigungs-E-Mail

Wenn ihr dem Absender eine Bestaetigung schicken wollt:

Nach der "Datei erstellen"-Aktion eine weitere Aktion hinzufuegen:

**"E-Mail senden (V2)"** (Office 365 Outlook)
- **An**: `@{triggerOutputs()?['body/from']}`
- **Betreff**: `Foto empfangen!`
- **Text**: `Dein Foto wurde erfolgreich hochgeladen und erscheint in Kuerze auf dem Bilderrahmen.`

> **Empfehlung**: Lieber weglassen. Die Familie wird sonst bei jedem Foto eine Bestaetigungs-E-Mail bekommen, was schnell nervt.

---

## 5. Flow-Uebersicht

```
E-Mail mit Foto-Anhang
        |
        v
  [Trigger: Neue E-Mail mit Anlage]
        |
        v
  [Fuer jede Anlage:]
        |
        v
  [Ist es ein Bild? (jpg/png/heic)]
       / \
     Ja    Nein
      |      |
      v      v
  [In OneDrive   [Ignorieren]
   speichern]
        |
        v
  [Graph API Webhook wird ausgeloest]
        |
        v
  [process_new_photo: EXIF extrahieren, Metadaten speichern]
        |
        v
  [Foto erscheint auf dem Bilderrahmen]
```

---

## 6. Kosten

Power Automate in Microsoft 365 enthalten:
- **Limit**: 6.000 Flow-Ausfuehrungen pro Monat (Standard M365 Lizenz)
- Bei 20 Familienmitgliedern, 5 Fotos pro Woche = ~400 Ausfuehrungen/Monat
- Weit unter dem Limit

---

## 7. Der Familie mitteilen

Wenn alles funktioniert, schicke der Familie eine kurze Nachricht:

> **Neuer Weg, Fotos auf Omas Bilderrahmen zu laden!**
> 
> Schickt einfach eine E-Mail mit Foto(s) an: bilderrahmen@family-domain.de
> 
> - Betreff = Bildunterschrift
> - Text = Beschreibung (optional)
> - Foto(s) als Anhang
> 
> Die Fotos erscheinen innerhalb weniger Minuten auf dem Bilderrahmen!
