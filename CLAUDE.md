# CLAUDE.md - Router Radio Controller Project

## Project Overview
**Goal**: Reliable, modular Selenium Python toolkit for automated control of a Netgear router's 2.4GHz radio via web interface.

## Core Requirements

### Functional Interface
- **Status Check**: Return `RADIO_ON`, `RADIO_OFF`, `NOT_CONNECTED_TO_ROUTER`, or `UNEXPECTED_FAILURE`
- **Turn Radio On**: Return `SUCCESS`, `ALREADY_ON`, `NOT_CONNECTED_TO_ROUTER`, or `UNEXPECTED_FAILURE`  
- **Turn Radio Off**: Return `SUCCESS`, `ALREADY_OFF`, `NOT_CONNECTED_TO_ROUTER`, or `UNEXPECTED_FAILURE`

### Technical Specifications
- **Platform**: macOS
- **Browser**: Chrome via Selenium WebDriver (headless support)
- **Network**: Must be connected to `1_lemonlemon_1` WiFi or wired ethernet
- **Router**: Netgear with admin panel at `https://routerlogin.net/`
- **Configuration**: YAML-based config with sensible defaults

## Architecture

### Modular Design
```
├── router_controller.py      # Main CLI and controller logic
├── models.py                 # Data models and enums
├── logger.py                 # Logging system
├── network.py                # Network connectivity validation
├── credentials.py            # Secure credential management
├── webdriver_manager.py      # Browser automation management
├── utils.py                  # Utilities and retry decorators
├── exceptions.py             # Custom exception hierarchy
└── config.example.yaml       # Configuration template
```

### Key Features
- **Retry Mechanism**: `@retry` decorator with configurable attempts and backoff
- **Headless Mode**: Background operation support
- **macOS Notifications**: Optional status change alerts
- **YAML Configuration**: File-based or programmatic config
- **Error Hierarchy**: Specific exceptions for better debugging

## Usage Patterns

### CLI Usage
```bash
# Basic operations
python router_controller.py status
python router_controller.py on
python router_controller.py off

# Advanced options
python router_controller.py on --headless --notifications
python router_controller.py status --config custom_config.yaml
```

### Configuration
Copy `config.example.yaml` to `~/.router_controller_config.yaml`:
```yaml
target_network: "1_lemonlemon_1"
headless: false
retry_attempts: 3
retry_delay: 2
enable_notifications: false
timeout: 10
```

### Programmatic Usage
```python
from router_controller import RouterController, RouterConfig

# Custom configuration
config = RouterConfig(headless=True, enable_notifications=True)

with RouterController(config) as controller:
    status = controller.check_radio_status()
    if status == RadioStatus.RADIO_OFF:
        result = controller.turn_on_radio()
```

## Implementation Details

### Security
- Credentials via macOS keychain system (`keyring` library, viewable in Passwords app)
- No sensitive data in logs or configuration files
- Secure-by-default design

### Reliability
- Retry mechanism for transient network issues
- Explicit waits instead of arbitrary delays
- Network connectivity validation before operations
- Context managers for automatic cleanup

### Maintainability
- Single-responsibility modules
- Type hints and comprehensive docstrings
- Custom exception hierarchy for specific error handling
- Configurable timeouts and behavior

## Router Navigation Flow
1. Navigate to `https://routerlogin.net/`
2. **Handle SSL Certificate Warning** (if present):
   - Detect Chrome's "Your connection is not private" page
   - Click "Advanced" button (`#details-button`)
   - Click "Proceed to routerlogin.net (unsafe)" link (`#proceed-link`)
3. Login with stored credentials
4. Navigate to `https://routerlogin.net/adv_index.htm`
5. Expand "Advanced Setup" section (`#advanced_bt`)
6. Check radio status via CSS classes on "Wireless Settings (2.4GHz)":
   - `img_status_good` = radio ON
   - `img_status_warning`/`img_status_error` = radio OFF
7. Click "Wireless Settings" (`#wladv`) to access controls
8. Toggle "Enable Wireless Router Radio" checkbox (`#enable_ap`)
9. Apply changes via "Apply" button (`#apply`)

## Dependencies
- `selenium>=4.15.0` - Browser automation
- `keyring>=24.3.0` - Secure credential storage
- `PyYAML>=6.0` - YAML configuration support (optional)