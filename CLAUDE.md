# Router Radio Controller

## Overview
Selenium-based tool for controlling Netgear router 2.4GHz radio via web interface.

## Architecture
```
├── router_controller.py      # Main CLI and controller
├── models.py                 # Data models and enums
├── logger.py                 # Logging system
├── network.py                # Network validation
├── credentials.py            # Keychain credential storage
├── webdriver_manager.py      # Chrome WebDriver management
├── utils.py                  # Retry decorator and notifications
├── exceptions.py             # Custom exceptions
└── config.example.yaml       # Configuration template
```

## Usage
```bash
python router_controller.py status
python router_controller.py on
python router_controller.py off
python router_controller.py on --headless --notifications
```

## Requirements
- macOS platform
- Chrome browser
- Connected to router network
- Router at `https://routerlogin.net/`

## Return Values
- **Status**: `RADIO_ON`, `RADIO_OFF`, `NOT_CONNECTED_TO_ROUTER`, `VPN_CONNECTED`, `UNEXPECTED_FAILURE`
- **Actions**: `SUCCESS`, `ALREADY_ON/OFF`, `NOT_CONNECTED_TO_ROUTER`, `VPN_CONNECTED`, `UNEXPECTED_FAILURE`

## Security
- Credentials stored in macOS Keychain via `keyring`
- No sensitive data in logs or config files