# Signage kiosk

Turn a Raspberry Pi 5 (or any Wayland/labwc box) into a fullscreen, chromeless
e-signage display that shows the latest landscape research poster from
[slop.university/signage/landscape](https://slop.university/signage/landscape/).

The route renders the poster PDF to a canvas and self-reloads hourly, so a fresh
publish appears on the display with no intervention. There is a matching
`/signage/portrait` route for a portrait-oriented screen --- point the launcher
at that instead.

## What's here

- `signage-kiosk-launch` --- launches one fullscreen Chromium at the signage
  URL. Install at `/usr/local/bin/` (executable, root-owned).
- `signage-kiosk.service` --- systemd **user** unit that runs the launcher once
  the Wayland session is up, and restarts it if Chromium dies.
- `signage-kiosk-restart.{service,timer}` --- restarts the kiosk daily at 04:00
  to clear any browser memory creep on a long-running display.
- `labwc-rc.xml` --- a labwc window rule that forces the kiosk window fullscreen
  on a chosen HDMI output.

None of these carry any host-, network-, or account-specific configuration ---
bring your own network setup and (optionally) remote access.

## Prerequisites

- Raspberry Pi OS Bookworm (or similar) with a **labwc / Wayland** session and
  Chromium installed.
- The display attached to one HDMI output. A Pi 5's HDMI is capped at 4K, but an
  8K panel will accept and upscale a 4K signal, which is ample for a poster.
- Network access to `slop.university` (configure however you like --- this repo
  intentionally ships no network config).

The site serves pdf.js's _legacy_ build, so even an older Chromium renders the
poster. A current Chromium is still recommended for security fixes; note the
`--password-store=basic` flag in the launcher, which suppresses the "create a
new keyring" dialog that recent Chromium otherwise shows in an auto-login
session.

## Install

Run as the unprivileged user that owns the graphical session (referred to below
as the _kiosk user_).

```bash
# 1. Launcher
sudo install -m 0755 signage-kiosk-launch /usr/local/bin/signage-kiosk-launch

# 2. systemd user units
mkdir -p ~/.config/systemd/user
install -m 0644 signage-kiosk.service signage-kiosk-restart.service \
    signage-kiosk-restart.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable signage-kiosk.service
systemctl --user enable --now signage-kiosk-restart.timer

# 3. labwc window rule --- set the HDMI output first (see the file's comment)
mkdir -p ~/.config/labwc
install -m 0644 labwc-rc.xml ~/.config/labwc/rc.xml
```

Then make labwc start the kiosk when the session comes up. In
`~/.config/labwc/autostart`:

```sh
systemctl --user start signage-kiosk.service &
```

Finally, configure your display manager to auto-login the kiosk user into the
labwc session on boot (e.g. LightDM `autologin-user` + `autologin-session`).

## Operate

```bash
# Restart after a config change
systemctl --user restart signage-kiosk.service

# Live logs
journalctl --user -u signage-kiosk -f

# What URL / poster is currently loaded (debug port)
curl -s http://localhost:9222/json/list | grep -o '"url":[^,]*'

# Screenshot the display (Wayland)
grim /tmp/signage.png
```

To change which output the poster shows on, edit the `output=` in
`~/.config/labwc/rc.xml` and `systemctl --user restart signage-kiosk`.
