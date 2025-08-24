# Router Radio Controller

Control your Netgear router's 2.4GHz radio via command line.

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

Uses Selenium WebDriver to automate Chrome browser:
1. Checks VPN status and network connectivity
2. Navigates to router admin panel (`https://routerlogin.net/`)
3. Handles SSL warnings and login authentication
4. Locates wireless settings in iframe content
5. Toggles 2.4GHz radio checkbox and applies changes

Self-contained executable manages Python environment and dependencies automatically.