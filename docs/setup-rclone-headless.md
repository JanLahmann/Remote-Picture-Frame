# rclone Headless OAuth for OneDrive

The Raspberry Pi Zero 2 W is headless (no desktop, no browser). rclone's
standard `rclone config` flow opens a browser for Microsoft OAuth, which
won't work over SSH. This guide covers how to authenticate rclone on a
headless Pi.

---

## Method 1: Remote Auth (recommended)

Use a second machine (laptop/desktop) that has a browser to complete the
OAuth flow, then transfer the token to the Pi.

### On your laptop (the machine with a browser):

1. **Install rclone** if not already installed:
   ```bash
   # macOS
   brew install rclone

   # Linux
   curl https://rclone.org/install.sh | sudo bash

   # Windows
   winget install Rclone.Rclone
   ```

2. **Run the authorization helper:**
   ```bash
   rclone authorize "onedrive"
   ```

3. A browser window opens. Sign in with the Microsoft account that has
   access to the FamilyFrame OneDrive folder.

4. After granting access, rclone prints a token blob to the terminal:
   ```
   Paste the following into your remote machine --->
   {"access_token":"eyJ0...","token_type":"Bearer","refresh_token":"0.AQ...","expiry":"..."}
   <---End paste
   ```

5. **Copy this entire JSON token** (everything between the arrows).

### On the Raspberry Pi (over SSH):

1. **Start rclone config:**
   ```bash
   rclone config
   ```

2. Choose `n` (New remote)

3. **Name:** `onedrive`

4. **Storage type:** Search for `onedrive` or enter its number

5. **Client ID:** Leave blank (press Enter) — uses rclone's default

6. **Client secret:** Leave blank (press Enter)

7. **Region:** Choose `1` (Microsoft Cloud Global)

8. **Edit advanced config?** `n`

9. **Use auto config?** `n` (this is the key step!)

10. **Paste the token** from step 5 above

11. **Choose drive type:** `1` (OneDrive Personal) or `2` (OneDrive Business)
    depending on your account

12. **Choose drive:** Usually `0` (the only one listed)

13. **Confirm:** `y`

14. **Test the connection:**
    ```bash
    rclone ls onedrive:/FamilyFrame/photos/ --max-depth 1
    ```

---

## Method 2: Copy Config from Another Machine

If you already have rclone configured on another machine with the same
OneDrive account:

1. **On the machine with working rclone:**
   ```bash
   rclone config file
   # Shows the config file path, e.g. ~/.config/rclone/rclone.conf
   cat ~/.config/rclone/rclone.conf
   ```

2. **Copy the `[onedrive]` section** from that file.

3. **On the Raspberry Pi:**
   ```bash
   mkdir -p ~/.config/rclone
   nano ~/.config/rclone/rclone.conf
   ```

4. Paste the `[onedrive]` section and save.

5. **Test:**
   ```bash
   rclone ls onedrive:/FamilyFrame/photos/ --max-depth 1
   ```

> **Note:** The OAuth token will eventually expire and rclone will
> automatically refresh it. If you see authentication errors months later,
> re-run Method 1.

---

## Method 3: SSH Tunnel (advanced)

Forward the OAuth callback from the Pi to your local browser:

1. **On the Pi,** start rclone config and answer `y` to auto config. It will
   start a local web server on port 53682 and wait.

2. **On your laptop,** open an SSH tunnel:
   ```bash
   ssh -L 53682:localhost:53682 pi@raspberrypi.local
   ```

3. **Open** `http://localhost:53682` in your laptop's browser.

4. Complete the Microsoft sign-in. The callback goes through the SSH tunnel
   back to rclone on the Pi.

> This method is trickier to get right and Method 1 is simpler. Only use
> this if you prefer not to install rclone on your laptop.

---

## Token Refresh and Expiry

- rclone's OneDrive token automatically refreshes every ~1 hour
- The refresh token itself lasts 90 days of inactivity
- As long as FamilyFrame syncs at least once every 90 days, the token stays
  valid indefinitely
- Since the sync timer runs every 5 minutes, this is never an issue in
  normal operation

### If the token expires (e.g. Pi was off for 3+ months):

Re-run Method 1 to get a fresh token:

```bash
# On your laptop:
rclone authorize "onedrive"

# On the Pi:
rclone config
# Select the existing remote → Edit → re-paste the token
```

---

## Troubleshooting

**"Failed to configure token" error:**
- Make sure you copied the entire JSON blob including the curly braces
- The token is only valid for a few minutes — re-run `rclone authorize` if
  it took too long

**"Auth failed" after months of working:**
- Token likely expired. Re-authorize with Method 1
- Check if the Microsoft account password was changed (invalidates tokens)

**"Access denied" to the folder:**
- Verify the folder path: `rclone lsd onedrive:/` lists root folders
- If using a shared folder, it may appear under a different path.
  Try: `rclone lsd onedrive:/` to see what's available

**rclone config file location:**
```bash
rclone config file
# Usually: /home/pi/.config/rclone/rclone.conf
```
