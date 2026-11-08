# Router Radio Controller

Turn a Netgear router's **2.4 GHz Wi-Fi radio** on and off from your Mac. Use the menu bar or the command line. Wired Ethernet keeps working either way.

Built for the Nighthawk BE9300 (RS300, firmware V1.2.7.2). It should work on other Netgear routers that use the same admin pages.

## Setup on a new Mac

```bash
xcode-select --install     # Apple's command-line tools, for the menu bar app (skip if installed)
git clone https://github.com/dcetlin/netgear-router-scraper-radio-interface.git router-radio-toggle
cd router-radio-toggle
./router_controller status # first run: sets up Python, asks for the router login, saves it to Keychain
menubar/build.sh           # builds and installs /Applications/Router Radio.app
open "/Applications/Router Radio.app"
```

**Before you start, you need:**
- Google Chrome installed.
- The Mac on the router's network, by Ethernet or its Wi-Fi.
- Any VPN turned off.

**When you're asked:**
- The router admin login is stored in the macOS Keychain under `router_admin`. It is never written to disk in the repo.
- macOS may ask once to let Router Radio access the folder the repo is in. Allow it.

## Menu bar app

**Router Radio** puts an antenna icon in the menu bar:

| Icon | Meaning |
|---|---|
| antenna | 2.4 GHz is **on** |
| antenna with a slash | 2.4 GHz is **off** |
| `…` | working (about 2s to check, about 7s to switch) |
| triangle | can't tell. Open the menu for the reason. |

Click the icon to **Turn On / Turn Off** or **Refresh**. It re-checks every 15 minutes, so the icon stays accurate if the radio is changed some other way.

To make it start at login: **System Settings → General → Login Items → +**, then choose Router Radio.

## Command line

```bash
./router_controller status   # 🟢 RADIO ON  or  🔴 RADIO OFF
./router_controller on       # ✅ SUCCESS   or  🔵 ALREADY ON
./router_controller off      # ✅ SUCCESS   or  🔵 ALREADY OFF
```

| Flag | Effect |
|---|---|
| `--headless` | hide Chrome during on/off |
| `--json` | print one line for scripts and apps: `{"action": "status", "result": "RADIO_OFF", "seconds": 2.0}` |
| `--notifications` | show a macOS notification after on/off |
| `--debug` | full log on screen; keeps Chrome open for inspection |

| Result | Means |
|---|---|
| `RADIO_ON` / `RADIO_OFF` | current state (`status`) |
| `SUCCESS` | changed, and the router confirmed it |
| `ALREADY_ON` / `ALREADY_OFF` | nothing to do |
| `NOT_CONNECTED_TO_ROUTER` | this Mac isn't on the router's network |
| `VPN_CONNECTED` | turn off the VPN and try again |
| `UNEXPECTED_FAILURE` | see `~/.router_controller.log`; rerun with `--debug` |

Settings are optional. Copy `config.example.yaml` to `~/.router_controller_config.yaml` to change any default.

## How it works

1. **Checks the network.** It stops if a VPN is on, or if the Mac isn't on the router's Wi-Fi or any wired connection.
2. **Reads the state over plain HTTP:** it logs in with the router's own form and reads the saved 2.4 GHz setting from `WLG_adv.htm`. No browser, about 2s. This is all `status` does.
3. **Changes it in headless Chrome:** if the radio isn't already in the requested state, it ticks "Enable Wireless Router Radio" on the real Advanced Wireless page and clicks Apply. A browser is needed because that page's JavaScript builds the 80-odd fields the router expects.
4. **Confirms over HTTP.** It reports `SUCCESS` only once the router reports the new state.
   - The router allows one admin session at a time, so any other login (a browser tab, another run) can end this one. If that happens, it logs in again, and it retries the Apply once.

`./router_controller` is a small launcher. It creates `venv/` and installs `requirements.txt` on first run, then calls `venv/bin/python` directly, so moving the folder doesn't break it.

## Files

```
router_controller          launcher (creates the venv, runs the CLI)
router_controller.py       CLI and controller
router_http.py             browser-free login and state read
credentials.py             Keychain storage for the admin login
network.py                 VPN and network checks
webdriver_manager.py       headless Chrome
logger.py, utils.py        logging, notifications, output formatting
models.py                  result codes and config
menubar/                   Router Radio menu bar app (SwiftUI) and its build script
script_editor_helpers/     older AppleScript launcher: pick on/off/status in a dialog
```
