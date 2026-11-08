# Router Radio Controller

Turns a Netgear router's 2.4 GHz radio on and off from macOS. Built for the Nighthawk BE9300 (RS300, firmware V1.2.7.2). README.md is the user-facing source of truth; this file is for working on the code.

## Shape
- `router_controller.py`: CLI (`status|on|off`, `--headless --json --notifications --debug`) and the controller.
  - **Reads** go over HTTP via `router_http.py`. It parses `con_endis_wl_radio` from `WLG_adv.htm`.
  - **Writes** use headless Chrome. It logs in with the real form, runs `goto_formframe('WLG_adv.htm')`, toggles `#enable_ap`, then clicks `#apply`.
  - **Every write is confirmed** by re-reading over HTTP.
- `menubar/RouterRadio.swift`: SwiftUI `MenuBarExtra`. It shells out to `router_controller ... --headless --json`. `menubar/build.sh` records the repo path in Info.plist (`RouterControllerPath`) and installs the app to /Applications.
- `router_controller` (bash): calls `venv/bin/python` directly. Never `source venv/bin/activate`: activate hardcodes the creation path and breaks when the folder moves.

## Router facts that shape the code
- **One admin session at a time.** A browser login ends the HTTP session. It can also void an Apply that's in flight. Hence the HTTP re-login, the single Apply retry, and the menu bar app's one-call-at-a-time guard.
- **The Advanced Wireless form's JS builds about 84 POST fields**, so don't hand-build that POST. Injecting the HTTP `jwt_local` cookie into Chrome doesn't authenticate.
- **Login** is a POST to `/apply.cgi?%20timestamp=<ts>` with `submit_flag=admin_login` and `password = base64(rand + base64(pw) + rand)`.

## Contracts
- **Result codes** (`models.py`): `RADIO_ON`, `RADIO_OFF`, `SUCCESS`, `ALREADY_ON`, `ALREADY_OFF`, `NOT_CONNECTED_TO_ROUTER`, `VPN_CONNECTED`, `UNEXPECTED_FAILURE`.
- **`--json` output** is exactly one stdout line. Anything else printed to stdout breaks the menu bar app, so:
  - The live progress line only draws on a TTY.
  - Selenium Manager stats are disabled (`SE_AVOID_STATS`).
- **Credentials** live only in the macOS Keychain (`router_admin` / `username`, `password`), read via `keyring`. Never log, print or commit them.

## Testing
- Use the real router, from a Mac on its network.
- `status` is safe to run any time. `on`/`off` change the live radio, so return it to the state you found it in.
- Test GUI changes with a stand-in script, not by sending keystrokes to someone's live screen.
