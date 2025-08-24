# Router Radio Controller

Elegant, reliable automation for controlling your Netgear router's 2.4GHz radio via web interface.

## Features

- ✅ **Simple CLI**: Check status, turn radio on/off with single commands
- ✅ **Secure**: Credentials stored in macOS Keychain, never in code
- ✅ **Reliable**: Retry mechanism handles transient network issues  
- ✅ **Headless**: Background operation support for automation
- ✅ **Configurable**: YAML config files with sensible defaults
- ✅ **Smart**: Validates network connection before attempting operations
- ✅ **SSL Handling**: Automatically bypasses router certificate warnings
- ✅ **Notifications**: Optional macOS alerts for status changes

## Quick Start

1. **Set up Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Connect to your router's network** (`1_lemonlemon_1` WiFi or ethernet)

3. **Run commands:**
   ```bash
   python router_controller.py status    # Check current state
   python router_controller.py on        # Enable 2.4GHz radio
   python router_controller.py off       # Disable 2.4GHz radio
   ```

4. **First run:** Enter router admin credentials when prompted (stored securely in macOS keychain)

> **Note:** Always activate the virtual environment (`source venv/bin/activate`) before running the script.

## Advanced Usage

**Remember to activate the virtual environment first:**
```bash
source venv/bin/activate  # Always run this first
```

**Then use advanced options:**
```bash
# Background operation (no browser window)
python router_controller.py on --headless

# Enable notifications
python router_controller.py off --notifications

# Custom configuration file
python router_controller.py status --config /path/to/config.yaml

# Get help
python router_controller.py -h
```

## Configuration

Copy `config.example.yaml` to `~/.router_controller_config.yaml`:

```yaml
target_network: "1_lemonlemon_1"    # Your router's network name
headless: false                     # Run browser in background
retry_attempts: 3                   # Retry failed operations
retry_delay: 2                      # Seconds between retries
enable_notifications: false         # macOS notifications
timeout: 10                         # WebDriver timeout
```

## Requirements

- **Platform**: macOS
- **Python**: 3.7+
- **Network**: Must be connected to router's WiFi or ethernet
- **Router**: Netgear with web interface at `https://routerlogin.net/`
- **Browser**: Chrome (automatically managed via Selenium)

## Programmatic Usage

```python
from router_controller import RouterController, RouterConfig

config = RouterConfig(headless=True, enable_notifications=True)

with RouterController(config) as controller:
    status = controller.check_radio_status()
    if status.value == "RADIO_OFF":
        result = controller.turn_on_radio()
        print(f"Result: {result.value}")
```

## Return Values

### Status Check
- `RADIO_ON` - 2.4GHz radio is active
- `RADIO_OFF` - 2.4GHz radio is disabled  
- `NOT_CONNECTED_TO_ROUTER` - Not on router's network
- `UNEXPECTED_FAILURE` - Error occurred

### Radio Control
- `SUCCESS` - Operation completed successfully
- `ALREADY_ON` / `ALREADY_OFF` - Radio already in desired state
- `NOT_CONNECTED_TO_ROUTER` - Not on router's network
- `UNEXPECTED_FAILURE` - Error occurred

## Architecture

```
├── router_controller.py      # Main CLI and controller
├── models.py                 # Data models and enums
├── logger.py                 # Logging system
├── network.py                # Network validation
├── credentials.py            # Secure credential storage
├── webdriver_manager.py      # Browser automation
├── utils.py                  # Utilities and retry logic
├── exceptions.py             # Custom exceptions
└── config.example.yaml       # Configuration template
```

## Troubleshooting

- **"Not connected to target network"**: Ensure you're on the router's WiFi or wired connection
- **Login fails**: Check router admin credentials, try accessing `https://routerlogin.net/` manually
- **Chrome driver issues**: Ensure Chrome browser is installed
- **Timeout errors**: Increase `timeout` value in config file

## Security

- Router credentials stored in macOS keychain via `keyring` library (viewable in Passwords app)
- No sensitive data in logs or configuration files  
- Network validation prevents unauthorized access attempts
- Secure by design, convenient by default

## Managing Credentials

- **View/Edit**: Open **Passwords** app → Search for "router_admin"
- **Delete**: Remove entries in Passwords app, or script will re-prompt
- **Manual Setup**: You can add entries manually in Passwords app with service "router_admin"

---

Built with Python, Selenium, and attention to reliability.