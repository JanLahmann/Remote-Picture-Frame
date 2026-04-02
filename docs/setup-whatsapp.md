# WhatsApp Upload einrichten (Meta WhatsApp Cloud API)

Die Familie kann Fotos per WhatsApp an eine dedizierte Nummer senden.
Die Fotos landen automatisch auf dem Bilderrahmen.

**Kosten: 0 EUR/Monat** (1.000 Konversationen/Monat im Free Tier)

---

## Voraussetzungen

- Ein persoenlicher Facebook-Account (kein Unternehmen noetig)
- Eine Telefonnummer fuer WhatsApp (z.B. Prepaid-SIM, ~5 EUR einmalig)
- Das FamilyFrame-Backend ist bereits deployed

---

## 1. Meta Business Portfolio erstellen

1. Gehe zu https://business.facebook.com
2. Klicke **Konto erstellen**
3. Fulle aus:
   - **Name des Unternehmens**: `FamilyFrame` (oder beliebig)
   - **Dein Name**: Dein Name
   - **E-Mail**: Deine E-Mail
4. Klicke **Absenden**

> Es wird nicht geprueft, ob es ein echtes Unternehmen ist.
> Fuer den Free Tier (Nachrichten empfangen) ist keine Verifizierung noetig.

---

## 2. Meta Developer App erstellen

1. Gehe zu https://developers.facebook.com
2. Klicke **Meine Apps** → **App erstellen**
3. Waehle:
   - **App-Typ**: Business
   - **App-Name**: `FamilyFrame`
   - **Business Portfolio**: Das eben erstellte Portfolio
4. Klicke **App erstellen**

---

## 3. WhatsApp-Produkt hinzufuegen

1. In der App-Uebersicht: **Produkte hinzufuegen** → **WhatsApp** → **Einrichten**
2. Waehle dein Business Portfolio
3. Du landest auf dem WhatsApp **Erste Schritte**-Dashboard

---

## 4. Telefonnummer registrieren

### Test-Nummer (zum Ausprobieren)

Meta stellt eine Test-Telefonnummer bereit. Damit kannst du sofort testen.
Einschraenkung: Du kannst nur an Nummern senden, die du vorher als "Testnummern" registriert hast.

### Eigene Nummer (fuer den Betrieb)

1. Im WhatsApp-Dashboard: **Erste Schritte** → **Telefonnummer hinzufuegen**
2. Gib die Nummer deiner Prepaid-SIM ein
3. Verifiziere per SMS oder Anruf
4. **Wichtig**: Diese Nummer kann danach NICHT mehr mit der normalen WhatsApp-App verwendet werden. Verwende eine dedizierte Prepaid-SIM.

---

## 5. Permanenten Access Token erstellen

Der im Dashboard angezeigte Token ist temporaer (24h). Fuer den Dauerbetrieb brauchst du einen permanenten Token:

1. Im Meta Developer Dashboard: **WhatsApp** → **Konfiguration**
2. Klicke **Permanenten Token generieren** (oder erstelle einen System-User):

### System User Token (empfohlen):

1. Gehe zu https://business.facebook.com → **Einstellungen** → **Personen** → **System-Users**
2. Klicke **Hinzufuegen** → Name: `FamilyFrame Bot`, Rolle: Admin
3. **Assets zuweisen** → Waehle deine WhatsApp-App → Berechtigung: **Alles verwalten**
4. **Token generieren**:
   - App: FamilyFrame
   - Berechtigungen: `whatsapp_business_messaging`, `whatsapp_business_management`
   - Token-Ablauf: **Nie**
5. **Token SOFORT kopieren** (wird nur einmal angezeigt!)

Dieser Token ist dein `WHATSAPP_ACCESS_TOKEN`.

---

## 6. Webhook konfigurieren

1. Im Meta Developer Dashboard: **WhatsApp** → **Konfiguration** → **Webhook**
2. Klicke **Bearbeiten**:
   - **Callback-URL**: `https://eu-de.functions.appdomain.cloud/api/v1/web/<namespace>/familyframe/whatsapp_webhook`
   - **Verify-Token**: Ein zufaelliger String deiner Wahl (z.B. `mein-geheimer-verify-token-2026`)
3. Klicke **Bestaetige und speichere**

   Meta sendet einen GET-Request an deine URL mit dem Verify-Token.
   Die `whatsapp_webhook`-Funktion antwortet automatisch mit dem Challenge-Token.

4. **Webhook-Felder abonnieren**: Klicke **Verwalten** → aktiviere:
   - `messages` (Nachrichten empfangen)

---

## 7. App Secret notieren

1. Im Meta Developer Dashboard: **Einstellungen** → **Allgemein**
2. Unter **App-Geheimnis**: Klicke **Anzeigen**
3. Kopiere den Wert → wird `WHATSAPP_APP_SECRET`

---

## 8. Backend konfigurieren

Fuege folgende Werte zu `backend/local.settings.json` hinzu:

```json
{
  "WHATSAPP_ACCESS_TOKEN": "dein-permanenter-access-token",
  "WHATSAPP_VERIFY_TOKEN": "mein-geheimer-verify-token-2026",
  "WHATSAPP_APP_SECRET": "dein-app-secret",
  "WHATSAPP_API_VERSION": "v21.0"
}
```

Dann neu deployen:

```bash
cd backend
./deploy.sh whatsapp_webhook
```

---

## 9. Testen

### Mit der Test-Nummer:

1. Im Meta Developer Dashboard: **WhatsApp** → **Erste Schritte**
2. Unter **Testnummern**: Fuege deine eigene WhatsApp-Nummer hinzu
3. Oeffne WhatsApp auf deinem Handy
4. Sende ein Foto an die Test-Nummer (wird im Dashboard angezeigt)
5. Pruefe ob das Foto in OneDrive `/FamilyFrame/photos/` angekommen ist

### Mit der eigenen Nummer:

1. Speichere die registrierte Nummer in deinem Telefon als "FamilyFrame"
2. Sende ein Foto mit einer Bildunterschrift als Nachricht
3. Das Foto sollte innerhalb von 1-2 Minuten auf dem Bilderrahmen erscheinen

---

## 10. Der Familie mitteilen

Schicke der Familie eine Nachricht:

> **Neuer Weg: Fotos per WhatsApp!**
>
> Speichert diese Nummer in eurem Telefon: **+49 XXX XXXXXXXX** (Name: "Omas Bilderrahmen")
>
> Schickt einfach ein Foto an diese Nummer.
> Optional: Schreibt eine Bildunterschrift dazu.
>
> Die Fotos erscheinen innerhalb weniger Minuten auf Omas Bilderrahmen!

---

## Fehlerbehebung

| Problem | Loesung |
|---------|---------|
| Webhook-Verifizierung schlaegt fehl | `WHATSAPP_VERIFY_TOKEN` in `local.settings.json` muss mit dem Wert im Meta Dashboard uebereinstimmen |
| Fotos kommen nicht an | IBM Cloud Functions Logs pruefen: `ibmcloud fn activation list --limit 10` dann `ibmcloud fn activation logs <id>` |
| `401 Unauthorized` beim Media-Download | Access Token abgelaufen? Neuen permanenten Token erstellen (Schritt 5) |
| Nachricht kommt an aber kein Foto | Nur Bild-Nachrichten werden verarbeitet. Text-only Nachrichten werden ignoriert. |
| "Dieses Unternehmen kann keine Nachrichten empfangen" | Nummer noch nicht verifiziert oder App noch im Development-Modus. Im Dashboard: **App-Modus** → **Live** schalten |

---

## Kosten-Uebersicht

| Posten | Kosten |
|--------|--------|
| Meta Business Portfolio | Kostenlos |
| Meta Developer App | Kostenlos |
| WhatsApp Cloud API (1.000 Konversationen/Monat) | Kostenlos |
| Prepaid-SIM (einmalig) | ~5 EUR |
| **Gesamt monatlich** | **0 EUR** |

Eine "Konversation" wird geoeffnet wenn ein Familienmitglied eine Nachricht sendet und dauert 24 Stunden. Bei 20 Familienmitgliedern mit je 5 Fotos/Woche = ~100 Konversationen/Monat — weit unter dem Limit von 1.000.
