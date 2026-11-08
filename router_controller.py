#!/usr/bin/env python3
"""Router 2.4GHz Radio Controller

Reads radio state over plain HTTP (about 2s, no browser). Flips it by driving
the router's own Advanced Wireless form in headless Chrome, because that form's
JavaScript assembles the 80-odd fields the router expects. Every change is
confirmed by re-reading the saved state from the router.
"""

import time
from datetime import datetime
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from models import RadioStatus, ActionResult, RouterConfig
from logger import Logger
from network import NetworkChecker
from credentials import CredentialManager
from webdriver_manager import WebDriverManager
from router_http import RouterHTTP
from utils import send_notification, format_status_output

WIRELESS_PAGE = "WLG_adv.htm"   # Advanced > Advanced Setup > Wireless Settings
RADIO_CHECKBOX = "enable_ap"    # "Enable Wireless Router Radio" for 2.4 GHz
CONFIRM_TIMEOUT = 15            # seconds to wait for the router to report the new state
ATTEMPTS = 2                    # a competing admin login can void an Apply; try once more


class RouterController:
    """Main controller for router radio management"""

    def __init__(self, config: RouterConfig = None):
        self.config = config or RouterConfig.from_yaml()
        self.logger = Logger(dynamic=not self.config.debug_mode, console=self.config.debug_mode)
        self.network_checker = NetworkChecker(self.logger, self.config.target_network)
        self.credential_manager = CredentialManager(self.logger, self.config.service_name)
        self.webdriver_manager = WebDriverManager(self.logger, self.config.headless, self.config.debug_mode)
        self.driver: Optional[webdriver.Chrome] = None
        self._http: Optional[RouterHTTP] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.clear_line()
        self.webdriver_manager.cleanup()

    # --- preconditions -------------------------------------------------

    def _ensure_network_connection(self) -> Tuple[bool, str]:
        """Verify network connectivity and VPN status"""
        if self.network_checker.is_vpn_connected():
            return False, "VPN_CONNECTED"
        if not self.network_checker.is_connected_to_target_network():
            self.logger.error("Not connected to target network")
            return False, "NOT_CONNECTED_TO_ROUTER"
        return True, "OK"

    def _get_credentials(self) -> Tuple[str, str]:
        username, password = self.credential_manager.get_credentials()
        if not username or not password:
            username, password = self.credential_manager.prompt_for_credentials()
        return username, password

    # --- reading state (no browser) -------------------------------------

    def _router(self) -> RouterHTTP:
        if self._http is None:
            username, password = self._get_credentials()
            self._http = RouterHTTP(self.config.router_url, username, password, self.config.timeout)
            self.logger.info("Logging in over HTTP")
            self._http.login()
        return self._http

    def _radio_enabled(self) -> bool:
        try:
            return self._router().radio_enabled()
        except Exception:
            # The router allows one admin session; a browser login (ours or anyone's) ends the
            # HTTP one. Log in again once before giving up.
            self.logger.debug("HTTP session ended, logging in again")
            self._http = None
            return self._router().radio_enabled()

    # --- changing state (browser) ---------------------------------------

    def _open_wireless_form(self):
        """Log in through the real login page, then load the wireless form into its frame."""
        username, password = self._get_credentials()
        self.driver = self.webdriver_manager.create_driver()
        wait = WebDriverWait(self.driver, max(self.config.timeout, 20))

        self.logger.info("Opening router login page")
        self.driver.get(self.config.router_url)
        wait.until(lambda d: d.find_elements(By.NAME, "username"))
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.execute_script("checklogin(document.forms[0])")

        wait.until(lambda d: "multi_login" in d.current_url or "unauth" in d.current_url
                   or d.execute_script("return typeof goto_formframe === 'function'"))
        if "multi_login" in self.driver.current_url:
            # Another admin session is open (e.g. a browser tab). Take over, as the UI's "Yes" does.
            self.logger.info("Another admin session is open, taking over")
            self.driver.find_element(By.ID, "yes").click()
            wait.until(lambda d: d.execute_script("return typeof goto_formframe === 'function'"))
        if "unauth" in self.driver.current_url:
            raise RuntimeError("Router rejected the login")

        self.logger.info("Opening wireless settings")
        self.driver.execute_script(f"goto_formframe('{WIRELESS_PAGE}')")
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "formframe")))
        return wait.until(lambda d: d.find_element(By.ID, RADIO_CHECKBOX))

    def _apply_radio(self, enable: bool) -> None:
        checkbox = self._open_wireless_form()
        if checkbox.is_selected() != enable:
            self.driver.execute_script("arguments[0].click()", checkbox)
        self.logger.info("Applying")
        self.driver.execute_script("arguments[0].click()", self.driver.find_element(By.ID, "apply"))
        time.sleep(0.5)
        try:  # some firmware versions confirm with a dialog
            self.driver.switch_to.alert.accept()
        except Exception:
            pass

    def _wait_for_state(self, enable: bool) -> bool:
        self.logger.info("Confirming with the router")
        deadline = time.time() + CONFIRM_TIMEOUT
        while time.time() < deadline:
            try:
                if self._radio_enabled() == enable:
                    return True
            except Exception as e:  # router briefly busy while it applies
                self.logger.debug(f"State check failed, retrying: {e}")
            time.sleep(1)
        return False

    def _set_radio(self, enable: bool) -> ActionResult:
        word = "on" if enable else "off"
        self.logger.info(f"Turning {word} 2.4GHz radio")

        ok, why = self._ensure_network_connection()
        if not ok:
            return ActionResult.VPN_CONNECTED if why == "VPN_CONNECTED" else ActionResult.NOT_CONNECTED_TO_ROUTER

        try:
            if self._radio_enabled() == enable:
                return ActionResult.ALREADY_ON if enable else ActionResult.ALREADY_OFF
            for attempt in range(1, ATTEMPTS + 1):
                self._apply_radio(enable)
                if self._wait_for_state(enable):
                    break
                self.logger.warning(f"Router did not report radio {word} (attempt {attempt}/{ATTEMPTS})")
                self.webdriver_manager.cleanup()
                self.driver = None
            else:
                return ActionResult.UNEXPECTED_FAILURE
        except Exception as e:
            self.logger.error(f"Failed to turn radio {word}: {e}")
            if self.config.debug_mode and self.driver:
                with open("/tmp/toggle_debug.html", "w") as f:
                    f.write(self.driver.page_source)
                self.logger.info("DEBUG: page source saved to /tmp/toggle_debug.html")
            return ActionResult.UNEXPECTED_FAILURE

        if self.config.enable_notifications:
            send_notification("Router Radio Controller", f"2.4GHz radio turned {word}")
        return ActionResult.SUCCESS

    # --- public API -----------------------------------------------------

    def check_radio_status(self) -> RadioStatus:
        """Check current radio status"""
        self.logger.info("Checking 2.4GHz radio status")
        ok, why = self._ensure_network_connection()
        if not ok:
            return RadioStatus.VPN_CONNECTED if why == "VPN_CONNECTED" else RadioStatus.NOT_CONNECTED_TO_ROUTER
        try:
            return RadioStatus.RADIO_ON if self._radio_enabled() else RadioStatus.RADIO_OFF
        except Exception as e:
            self.logger.error(f"Unexpected error checking radio status: {e}")
            return RadioStatus.UNEXPECTED_FAILURE

    def turn_on_radio(self) -> ActionResult:
        return self._set_radio(True)

    def turn_off_radio(self) -> ActionResult:
        return self._set_radio(False)


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Control Netgear router 2.4GHz radio",
        epilog="Examples:\n  status    Check radio status\n  on        Turn radio on\n  off       Turn radio off",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("action", choices=["status", "on", "off"], help="Action to perform")
    parser.add_argument("--headless", action="store_true", help="Run in background")
    parser.add_argument("--config", type=str, metavar="PATH", help="Custom config file")
    parser.add_argument("--notifications", action="store_true", help="Enable notifications")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--json", action="store_true", help="Print one JSON line (for apps and scripts)")
    args = parser.parse_args()

    start_time = datetime.now()

    if args.config:
        from pathlib import Path
        config = RouterConfig.from_yaml(Path(args.config))
    else:
        config = RouterConfig.from_yaml()
    if args.headless:
        config.headless = True
    if args.notifications:
        config.enable_notifications = True
    if args.debug:
        config.debug_mode = True

    with RouterController(config) as controller:
        if args.action == "status":
            result = controller.check_radio_status()
        elif args.action == "on":
            result = controller.turn_on_radio()
        else:
            result = controller.turn_off_radio()
    seconds = round((datetime.now() - start_time).total_seconds(), 1)
    if args.json:
        import json
        print(json.dumps({"action": args.action, "result": result.value, "seconds": seconds}))
    else:
        print(format_status_output(result.value, args.action))
        print(f"Total Time: {seconds:.1f}s")


if __name__ == "__main__":
    main()
