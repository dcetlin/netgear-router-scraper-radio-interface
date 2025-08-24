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

## Brief Explanation of Implementation

Uses Selenium WebDriver to automate Chrome browser:
1. Checks VPN status and network connectivity
2. Navigates to router admin panel (`https://routerlogin.net/`)
3. Handles SSL warnings and login authentication
4. Locates wireless settings in iframe content
5. Toggles 2.4GHz radio checkbox and applies changes

Self-contained executable manages Python environment and dependencies automatically.