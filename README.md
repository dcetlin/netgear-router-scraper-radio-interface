# Router Radio Controller

Control your Netgear router's 2.4GHz radio via command line.

## Setup on a new Mac

Everything is in this repo except your router login, which stays in the Keychain.

```bash
xcode-select --install          # Swift compiler for the menu bar app (skip if already installed)
git clone https://github.com/dcetlin/netgear-router-scraper-radio-interface.git router-radio-toggle
cd router-radio-toggle
./router_controller status      # first run: builds the venv, then asks for the router admin login and saves it to Keychain
menubar/build.sh                # builds and installs /Applications/Router Radio.app
open "/Applications/Router Radio.app"
```

Needs Google Chrome, and the Mac must be on the router's network (Ethernet or its Wi-Fi). Optional settings go in `~/.router_controller_config.yaml` (see `config.example.yaml`); the defaults work for the BE9300.

## Usage

```bash
./router_controller status    # Check radio status
./router_controller on        # Turn radio on  
./router_controller off       # Turn radio off
```

**Requirements:**
- macOS with Chrome
- Connected to router network
- Disconnect VPN if active

First run prompts for router credentials (stored in macOS Keychain).

## Options

```bash
./router_controller status --headless        # Run in background
./router_controller on --notifications       # Enable notifications
./router_controller off --debug             # Debug mode
```

## Configuration

Optional `~/.router_controller_config.yaml`:

```yaml
target_network: "Your_WiFi_Name"
headless: false
timeout: 10
enable_notifications: false
```

## Status Output

```
🟢 RADIO ON    🔴 RADIO OFF    🔒 VPN DETECTED    ❌ FAILED
```

## Menu Bar App (recommended)

`menubar/` holds **Router Radio**, a tiny native menu bar app (SwiftUI, built with `swiftc`, no Xcode). The icon shows whether the 2.4GHz radio is on or off; click it for Turn On / Turn Off / Refresh. It runs `router_controller ... --json` underneath and re-checks every 15 minutes.

```bash
menubar/build.sh    # builds and installs /Applications/Router Radio.app
```

First launch asks for access to Documents (where this repo lives); allow it once.

## JSON Output

`--json` prints one line for scripts and apps: `{"action": "status", "result": "RADIO_OFF", "seconds": 2.0}`

## Create macOS Apps for Easy Access

Create clickable apps for Dock/Spotlight access using **Script Editor**:

1. Open **Script Editor** app (found in Applications/Utilities)
2. Use the template script in `/script_editor_helpers/`
3. Update the path and save as Application (.app)

This creates three `.app` bundles:
- **Router Radio Status.app** - Check radio status
- **Router Radio On.app** - Turn radio on
- **Router Radio Off.app** - Turn radio off

Apps automatically enable notifications and can be:
- Dragged to Dock for one-click access
- Found via Spotlight search ("Router Radio")
- Double-clicked from Finder

## Brief Explanation of Implementation

1. Checks VPN status and that the Mac is on the router's network (Wi-Fi or Ethernet)
2. Logs in over plain HTTP and reads the saved 2.4GHz state from `WLG_adv.htm` (about 2s, no browser). This is all `status` does.
3. For `on`/`off`, if the radio isn't already in that state: logs in through the real login page in headless Chrome, opens Advanced Wireless Settings, flips "Enable Wireless Router Radio" and clicks Apply. The browser is needed because that form's JavaScript builds the 80-odd fields the router expects.
4. Confirms the change by re-reading the state over HTTP. Reports SUCCESS only once the router says so.

Typical times on the BE9300 (firmware V1.2.7.2): status ~2s, on/off ~7s, already on/off ~2s.

Self-contained executable manages Python environment and dependencies automatically.
