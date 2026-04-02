# IBM Cloud & Microsoft Graph API Setup

Diese Anleitung beschreibt die Einrichtung aller Cloud-Dienste für FamilyFrame.

---

## 1. IBM Cloud Account erstellen

1. Gehe zu https://cloud.ibm.com/registration
2. Erstelle einen kostenlosen Account (Lite Plan, keine Kreditkarte noetig)
3. Nach dem Login: notiere dir deine **Region** (z.B. `eu-de` fuer Frankfurt)

## 2. IBM Cloud CLI installieren

```bash
# macOS
brew install ibmcloud-cli

# Linux
curl -fsSL https://clis.cloud.ibm.com/install/linux | sh

# Windows
# Download von https://github.com/IBM-Cloud/ibm-cloud-cli-release/releases
```

Anmelden und Plugins installieren:

```bash
ibmcloud login
ibmcloud target -r eu-de -g Default
ibmcloud plugin install cloud-functions
ibmcloud plugin install cloudant
```

## 3. IBM Cloudant Datenbank einrichten

### Ueber die Web-Konsole

1. Gehe zu https://cloud.ibm.com/catalog/services/cloudant
2. Waehle:
   - **Plan**: Lite (kostenlos)
   - **Region**: eu-de (Frankfurt)
   - **Authentication**: IAM and legacy credentials
3. Klicke **Create**
4. Oeffne den erstellten Service → **Service credentials** → **New credential**
5. Notiere dir:
   - `url` → wird `CLOUDANT_URL`
   - `apikey` → wird `CLOUDANT_APIKEY`

### Oder ueber die CLI

```bash
# Cloudant-Instanz erstellen
ibmcloud resource service-instance-create familyframe-db cloudantnosqldb lite eu-de \
  -p '{"legacyCredentials": false}'

# Service-Key erstellen
ibmcloud resource service-key-create familyframe-db-key Manager \
  --instance-name familyframe-db

# Credentials anzeigen
ibmcloud resource service-key familyframe-db-key
```

## 4. Microsoft Entra ID App Registration (fuer Graph API)

Die Graph API wird benoetigt, um auf OneDrive zuzugreifen — unabhaengig davon, welche Cloud das Backend hostet.

### 4.1 App registrieren

1. Gehe zu https://entra.microsoft.com → **Applications** → **App registrations**
2. Klicke **New registration**:
   - **Name**: `FamilyFrame Backend`
   - **Supported account types**: "Accounts in this organizational directory only" (Single tenant)
   - **Redirect URI**: leer lassen
3. Klicke **Register**
4. Notiere dir:
   - **Application (client) ID** → wird `GRAPH_CLIENT_ID`
   - **Directory (tenant) ID** → wird `GRAPH_TENANT_ID`

### 4.2 Client Secret erstellen

1. Im App-Registrierungsmenu: **Certificates & secrets** → **New client secret**
2. **Description**: `FamilyFrame Production`
3. **Expires**: 24 months
4. Klicke **Add**
5. **SOFORT den Value kopieren** (wird nur einmal angezeigt!) → wird `GRAPH_CLIENT_SECRET`

### 4.3 API-Berechtigungen setzen

1. Im App-Registrierungsmenu: **API permissions** → **Add a permission**
2. Waehle **Microsoft Graph** → **Application permissions**
3. Fuege folgende Berechtigungen hinzu:
   - `Files.Read.All` — Dateien lesen
   - `Files.ReadWrite.All` — Dateien schreiben (fuer WhatsApp-Upload)
   - `User.Read.All` — Benutzerinfos lesen (fuer "uploaded by")
4. Klicke **Grant admin consent for [Tenant]** (erfordert Admin-Rechte)

> **Sicherheitshinweis**: `Files.ReadWrite.All` ist eine breite Berechtigung. 
> Fuer zusaetzliche Sicherheit kann man spaeter auf Application Access Policies 
> einschraenken, sodass die App nur auf das OneDrive eines bestimmten Users 
> (z.B. familyframe@outlook.com) zugreifen kann.

### 4.4 (Optional) Application Access Policy einschraenken

Damit die App nur auf das FamilyFrame-OneDrive zugreifen kann:

```powershell
# In PowerShell mit Exchange Online Management Module:
New-ApplicationAccessPolicy `
  -AppId "<GRAPH_CLIENT_ID>" `
  -PolicyScopeGroupId "familyframe@outlook.com" `
  -AccessRight RestrictAccess `
  -Description "FamilyFrame: nur Zugriff auf FamilyFrame-Konto"
```

## 5. IBM Cloud Functions Namespace einrichten

```bash
# Namespace erstellen
ibmcloud fn namespace create familyframe --description "FamilyFrame Digital Picture Frame"

# Namespace auswaehlen
ibmcloud fn namespace target familyframe
```

## 6. IBM Cloud Object Storage (fuer PWA-Hosting)

### Instanz erstellen

```bash
ibmcloud resource service-instance-create familyframe-hosting \
  cloud-object-storage lite
```

### Bucket fuer statisches Hosting

1. Gehe zu https://cloud.ibm.com/objectstorage → Instanz oeffnen
2. **Create bucket** → **Custom bucket**:
   - **Name**: `familyframe-pwa`
   - **Resiliency**: Regional
   - **Location**: eu-de
3. Bucket oeffnen → **Configuration** → **Static website hosting**: Enable
   - Index document: `index.html`
   - Error document: `index.html` (fuer SPA-Routing)
4. **Access policies** → **Public access**: Enable

Die PWA ist dann erreichbar unter:
```
https://s3.eu-de.cloud-object-storage.appdomain.cloud/familyframe-pwa/
```

Oder mit einer eigenen Domain (optional):
1. CNAME DNS-Eintrag: `frame.deine-domain.de` → `s3.eu-de.cloud-object-storage.appdomain.cloud`
2. TLS-Zertifikat ueber Let's Encrypt oder IBM Certificate Manager

## 7. Konfiguration zusammenstellen

Erstelle die Datei `backend/local.settings.json` mit den gesammelten Werten:

```json
{
  "CLOUDANT_URL": "https://xxx.cloudantnosqldb.appdomain.cloud",
  "CLOUDANT_APIKEY": "dein-cloudant-api-key",
  "CLOUDANT_DB_NAME": "familyframe",
  "GRAPH_CLIENT_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "GRAPH_CLIENT_SECRET": "dein-client-secret",
  "GRAPH_TENANT_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "ONEDRIVE_USER_ID": "familyframe@outlook.com",
  "ONEDRIVE_FOLDER_PATH": "/FamilyFrame/photos",
  "WEBHOOK_URL": "https://eu-de.functions.appdomain.cloud/api/v1/web/xxx/familyframe/process_new_photo",
  "DEVICE_TOKEN": "ein-zufaelliger-token-fuer-tablet-auth",
  "THUMBNAIL_MAX_SIZE": "800"
}
```

Generiere einen sicheren Device Token:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 8. Backend deployen

```bash
cd backend
./deploy.sh
```

Das Skript gibt dir am Ende die Endpoint-URLs aus. Die `display_sync_api`-URL brauchst du fuer die PWA-Konfiguration.

## 9. PWA bauen und deployen

```bash
cd display-app

# Environment-Variablen setzen
echo 'VITE_API_BASE=https://eu-de.functions.appdomain.cloud/api/v1/web/xxx/familyframe' > .env.production
echo 'VITE_DEVICE_TOKEN=dein-device-token' >> .env.production

# Bauen
npm install
npm run build

# Hochladen zu IBM Cloud Object Storage
ibmcloud cos upload --bucket familyframe-pwa --key index.html --file dist/index.html --content-type "text/html"
# ... oder mit dem AWS CLI (kompatibel mit IBM COS):
aws s3 sync dist/ s3://familyframe-pwa/ --endpoint-url https://s3.eu-de.cloud-object-storage.appdomain.cloud
```

## 10. Graph API Webhook aktivieren

Rufe die `refresh_subscription`-Funktion einmal manuell auf, um den ersten Webhook zu erstellen:

```bash
ibmcloud fn action invoke familyframe/refresh_subscription --result
```

Die Ausgabe sollte so aussehen:
```json
{
  "action": "created",
  "subscription_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "expiration": "2026-04-05T03:00:00Z"
}
```

Ab jetzt wird der Webhook taeglich automatisch erneuert.

---

## Fehlerbehebung

| Problem | Loesung |
|---------|---------|
| `401 Unauthorized` bei Graph API | Client Secret abgelaufen? Neues erstellen unter Entra ID → App → Certificates & secrets |
| Webhook-Benachrichtigungen kommen nicht an | `ibmcloud fn action invoke familyframe/refresh_subscription --result` ausfuehren |
| Cloudant `429 Too Many Requests` | Lite Plan hat 20 reads/sec — fuer 1 Frame mehr als genug. Falls noetig: Standard Plan |
| PWA laedt nicht | CORS-Header pruefen: `display_sync_api` muss `Access-Control-Allow-Origin` setzen |
