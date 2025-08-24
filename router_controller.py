#!/usr/bin/env python3
"""
Router 2.4GHz Radio Controller
A composable, elegant script for managing router radio settings via Selenium.
"""

import time
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from models import RadioStatus, ActionResult, RouterConfig
from logger import Logger
from network import NetworkChecker
from credentials import CredentialManager
from webdriver_manager import WebDriverManager
from utils import retry, send_notification
from exceptions import NetworkConnectionError, AuthenticationError, RouterUIError




class RouterController:
    """Main controller for router radio management"""
    
    def __init__(self, config: RouterConfig = None):
        self.config = config or RouterConfig.from_yaml()
        self.logger = Logger()
        self.network_checker = NetworkChecker(self.logger, self.config.target_network)
        self.credential_manager = CredentialManager(self.logger, self.config.service_name)
        self.webdriver_manager = WebDriverManager(self.logger, self.config.headless, self.config.debug_mode)
        self.driver: Optional[webdriver.Chrome] = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.webdriver_manager.cleanup()
    
    def _ensure_network_connection(self) -> bool:
        """Verify network connectivity"""
        if not self.network_checker.is_connected_to_target_network():
            self.logger.error("Not connected to target network")
            return False
        return True
    
    def _get_credentials(self) -> Tuple[str, str]:
        """Get admin credentials"""
        username, password = self.credential_manager.get_credentials()
        if not username or not password:
            username, password = self.credential_manager.prompt_for_credentials()
        return username, password
    
    def _initialize_driver(self):
        """Initialize WebDriver if needed"""
        if not self.driver:
            self.driver = self.webdriver_manager.create_driver()
    
    def _handle_ssl_warning(self) -> bool:
        """Handle Chrome SSL certificate warning page"""
        try:
            wait = WebDriverWait(self.driver, 5)  # Shorter timeout for SSL check
            
            # Check if we're on the SSL warning page
            if "Your connection is not private" in self.driver.page_source:
                self.logger.info("SSL certificate warning detected, proceeding through warning")
                
                # Click "Advanced" button
                advanced_button = wait.until(EC.element_to_be_clickable((By.ID, "details-button")))
                advanced_button.click()
                self.logger.debug("Clicked Advanced button")
                time.sleep(1)
                
                # Click "Proceed to routerlogin.net (unsafe)" link
                proceed_link = wait.until(EC.element_to_be_clickable((By.ID, "proceed-link")))
                proceed_link.click()
                self.logger.info("Clicked proceed link, bypassing SSL warning")
                time.sleep(2)
                
                return True
            
            return True  # No SSL warning found
            
        except TimeoutException:
            self.logger.debug("No SSL warning page detected or elements not found")
            return True  # Assume no SSL warning if elements not found
        except Exception as e:
            self.logger.warning(f"Error handling SSL warning: {e}")
            return True  # Continue anyway

    @retry(tries=3, delay=2)
    def _login_to_router(self) -> bool:
        """Login to router admin panel"""
        try:
            self.logger.info("Navigating to router login page")
            self.driver.get(self.config.router_url)
            
            # Handle potential SSL certificate warning
            if not self._handle_ssl_warning():
                self.logger.error("Failed to handle SSL warning")
                return False
            
            username, password = self._get_credentials()
            
            # Wait for and fill login form
            wait = WebDriverWait(self.driver, self.config.timeout)
            username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # Submit login - Router uses <a> tag with onclick, not input[type='submit']
            login_button = self.driver.find_element(By.CSS_SELECTOR, "a[onclick*='login']")
            login_button.click()
            
            self.logger.info("Login submitted, waiting for page load")
            time.sleep(3)  # Give more time for potential redirects
            
            # Check if we got redirected to multi-login page
            current_url = self.driver.current_url
            if "multi_login" in current_url.lower():
                self.logger.info("Multi-login detected, handling concurrent session...")
                
                # Debug: save multi-login page
                if self.config.debug_mode:
                    with open('/tmp/multi_login_debug.html', 'w') as f:
                        f.write(self.driver.page_source)
                    self.logger.info("DEBUG: Multi-login page saved to /tmp/multi_login_debug.html")
                
                try:
                    # Look for "Yes" button to kick out other session (based on actual multi-login page)
                    yes_selectors = [
                        "#yes",  # Primary: the actual Yes button ID
                        "div[onclick*='login']",  # The Yes button has onclick="login()"
                        "div:contains('Yes')",  # Fallback: any div containing "Yes"
                        "input[value*='Yes']",
                        "input[value*='yes']", 
                        "input[value*='OK']",
                        "button[type='submit']",
                        "input[type='submit']"
                    ]
                    
                    for selector in yes_selectors:
                        try:
                            yes_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            yes_button.click()
                            self.logger.info(f"Clicked proceed button: {selector}")
                            time.sleep(3)
                            # Check if we successfully got past multi-login
                            new_url = self.driver.current_url
                            self.logger.info(f"After multi-login handling, current URL: {new_url}")
                            break
                        except:
                            continue
                            
                except Exception as e:
                    self.logger.warning(f"Failed to handle multi-login: {e}")
                    
            # Check if we're still on login page (login failed)
            elif "login" in current_url.lower():
                # Additional check: make sure we're actually on login page, not just a URL with "login" in it
                if self.driver.find_elements(By.NAME, "username") and self.driver.find_elements(By.NAME, "password"):
                    self.logger.warning("Still on login page after submission, login may have failed")
                    return False
            
            # Final success check: look for admin panel indicators
            if any(indicator in self.driver.page_source.lower() for indicator in ['advanced', 'setup', 'wireless', 'router']):
                self.logger.info("Successfully logged into admin panel")
                return True
                
            return True
            
        except TimeoutException:
            self.logger.error("Login page did not load within timeout")
            return False
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False
    
    def _navigate_to_advanced_settings(self) -> bool:
        """Navigate to advanced settings page"""
        try:
            self.logger.info("Navigating to advanced settings")
            self.driver.get(self.config.admin_url)
            
            wait = WebDriverWait(self.driver, self.config.timeout)
            
            # Expand Advanced Setup
            try:
                advanced_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "advanced_bt"))
                )
                advanced_button.click()
            except Exception as e:
                self.logger.error(f"Failed to find Advanced Setup button: {e}")
                if self.config.debug_mode:
                    # Debug: save page to see what we're actually looking at
                    with open('/tmp/admin_page_debug.html', 'w') as f:
                        f.write(self.driver.page_source)
                    self.logger.info("DEBUG: Admin page saved to /tmp/admin_page_debug.html")
                raise
            self.logger.info("Advanced Setup button clicked, waiting for content to load...")
            
            # Give a brief wait for the page to start loading content
            time.sleep(2)
            
            # Check iframes first (where content typically loads for this router)
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for i, iframe in enumerate(iframes):
                try:
                    self.logger.debug(f"Checking iframe {i}")
                    self.driver.switch_to.frame(iframe)
                    # Use shorter wait since we know content loads quickly
                    iframe_wait = WebDriverWait(self.driver, 6)
                    iframe_wait.until(EC.presence_of_element_located((By.ID, "content_icons")))
                    self.logger.info(f"Advanced settings content found in iframe {i}")
                    return True
                except:
                    self.driver.switch_to.default_content()
                    continue
            
            # Fallback: try main page if not found in iframes
            self.logger.debug("content_icons not in iframes, checking main page...")
            quick_wait = WebDriverWait(self.driver, 3)
            try:
                quick_wait.until(EC.presence_of_element_located((By.ID, "content_icons")))
                self.logger.info("Advanced settings content loaded in main page")
                return True
            except:
                pass
            
            # Final fallback with longer wait
            self.logger.debug("Trying longer wait as final fallback...")
            long_wait = WebDriverWait(self.driver, 10)
            long_wait.until(EC.presence_of_element_located((By.ID, "content_icons")))
            self.logger.info("Advanced settings content loaded (fallback)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to advanced settings: {e}")
            return False
    
    def _get_radio_status_from_ui(self) -> RadioStatus:
        """Check radio status from UI elements"""
        try:
            wait = WebDriverWait(self.driver, self.config.timeout)
            
            # Debug: Save page source for inspection
            if self.config.debug_mode:
                with open('/tmp/router_admin_page_debug.html', 'w') as f:
                    f.write(self.driver.page_source)
                self.logger.info("DEBUG: Admin page source saved to /tmp/router_admin_page_debug.html")
            
            self.logger.debug("Looking for 2.4GHz Wireless Settings status in content area...")
            
            # First try to find content_icons div which contains all the status information
            try:
                content_div = self.driver.find_element(By.ID, "content_icons")
                self.logger.debug("Found content_icons div")
            except:
                # If content_icons not found, the advanced section may not be expanded yet
                # Try to wait a bit more or look for it in frames
                self.logger.debug("content_icons not found, checking for iframe/frame")
                
                # Check if there's an iframe we need to switch to
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                if iframes:
                    self.logger.debug(f"Found {len(iframes)} iframes, switching to first one")
                    self.driver.switch_to.frame(iframes[0])
                    time.sleep(1)
                    try:
                        content_div = self.driver.find_element(By.ID, "content_icons")
                        self.logger.debug("Found content_icons in iframe")
                    except:
                        self.driver.switch_to.default_content()
                        raise Exception("content_icons not found in iframe either")
                else:
                    raise Exception("No content_icons div or iframes found")
            
            # Now look for the 2.4GHz wireless settings within content_icons
            # Based on your HTML: <div id="title_bgn" class="adv_icon">
            wireless_section = content_div.find_element(By.ID, "title_bgn")
            self.logger.debug("Found title_bgn section (2.4GHz Wireless Settings)")
            
            # Look for the status indicator within this section
            # Structure: <div id="words_title" class="title_doubleline">...<div class="img_status_*"></div>
            title_div = wireless_section.find_element(By.ID, "words_title")
            status_element = title_div.find_element(By.XPATH, ".//div[starts-with(@class, 'img_status')]")
            status_class = status_element.get_attribute("class")
            
            self.logger.debug(f"Found status element with class: {status_class}")
            
            # Check status based on the class from your HTML
            if "img_status_good" in status_class:
                self.logger.info("Radio status: ON (img_status_good)")
                return RadioStatus.RADIO_ON
            elif "img_status_error" in status_class:
                self.logger.info("Radio status: OFF (img_status_error)")
                return RadioStatus.RADIO_OFF
            elif "img_status_warning" in status_class:
                self.logger.info("Radio status: OFF (img_status_warning)")
                return RadioStatus.RADIO_OFF
            else:
                self.logger.warning(f"Unexpected status class: {status_class}")
                return RadioStatus.UNEXPECTED_FAILURE
                
        except Exception as e:
            self.logger.error(f"Failed to check radio status: {e}")
            if self.config.debug_mode:
                import traceback
                self.logger.debug(f"Full traceback: {traceback.format_exc()}")
                
                # Additional debug: try to find any img_status elements
                try:
                    status_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'img_status')]")
                    self.logger.debug(f"Found {len(status_elements)} img_status elements total")
                    for i, elem in enumerate(status_elements[:5]):
                        self.logger.debug(f"  Status element {i}: class='{elem.get_attribute('class')}', parent='{elem.find_element(By.XPATH, '..').get_attribute('id')}'")
                except Exception as debug_e:
                    self.logger.debug(f"Debug search failed: {debug_e}")
                    
            return RadioStatus.UNEXPECTED_FAILURE
    
    def _toggle_radio(self, enable: bool) -> ActionResult:
        """Toggle radio on/off"""
        try:
            wait = WebDriverWait(self.driver, self.config.timeout)
            
            # First, make sure we have the content area loaded (same as status check)
            try:
                content_div = self.driver.find_element(By.ID, "content_icons")
                self.logger.debug("Found content_icons div for toggle")
            except:
                # Check if content is in an iframe
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                if iframes:
                    self.logger.debug(f"Switching to iframe for toggle")
                    self.driver.switch_to.frame(iframes[1])  # Usually the content iframe
                    time.sleep(1)
                    try:
                        content_div = self.driver.find_element(By.ID, "content_icons")
                        self.logger.debug("Found content_icons in iframe for toggle")
                    except:
                        self.driver.switch_to.default_content()
                        raise Exception("content_icons not found for toggle")
                else:
                    raise Exception("No content_icons div found for toggle")
            
            # Click on the "Wireless Settings" link in the navigation menu
            # Based on HTML: <dt id="wladv" class="middle_name"><a target="formframe" onclick="click_adv_action('wladv');">
            # First switch back to default content to access the navigation menu
            self.driver.switch_to.default_content()
            
            self.logger.info("Clicking Wireless Settings link to navigate to configuration page")
            wireless_link = wait.until(EC.element_to_be_clickable((By.ID, "wladv")))
            wireless_link.click()
            time.sleep(3)  # Wait for navigation
            
            # The wireless configuration form loads into a frame called "formframe"
            # Switch to the formframe to access the actual wireless settings
            try:
                self.logger.debug("Switching to formframe to access wireless configuration")
                formframe = wait.until(EC.presence_of_element_located((By.NAME, "formframe")))
                self.driver.switch_to.frame(formframe)
                time.sleep(2)  # Wait for form content to load
            except Exception as e:
                self.logger.warning(f"Could not find formframe: {e}")
                # Try by index if name doesn't work
                iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                for i, iframe in enumerate(iframes):
                    if "form" in iframe.get_attribute("name").lower():
                        self.driver.switch_to.frame(iframe)
                        self.logger.debug(f"Switched to iframe {i} for wireless config")
                        time.sleep(2)
                        break
            
            # Now we should be in the wireless configuration frame
            # Look for the "Enable Wireless Router Radio" checkbox
            # Based on HTML: <input type="checkbox" name="enable_ap" id="enable_ap" value="1" onclick="check_schedule_onoff();">
            self.logger.debug("Looking for Enable Wireless Router Radio checkbox")
            try:
                checkbox = wait.until(EC.presence_of_element_located((By.ID, "enable_ap")))
                self.logger.debug("Found radio enable checkbox with ID: enable_ap")
            except:
                # Fallback selectors
                checkbox_selectors = [
                    "input[name='enable_ap']",
                    "input[type='checkbox'][value='1']",
                    "tr#ap_bgn input[type='checkbox']"
                ]
                
                checkbox = None
                for selector in checkbox_selectors:
                    try:
                        checkbox = self.driver.find_element(By.CSS_SELECTOR, selector)
                        self.logger.debug(f"Found radio enable checkbox using fallback: {selector}")
                        break
                    except:
                        continue
                
                if not checkbox:
                    raise Exception("Could not find radio enable checkbox")
            
            is_currently_enabled = checkbox.is_selected()
            self.logger.info(f"Current radio state: {'ON' if is_currently_enabled else 'OFF'}")
            
            if enable and is_currently_enabled:
                self.logger.info("Radio already enabled")
                return ActionResult.ALREADY_ON
            elif not enable and not is_currently_enabled:
                self.logger.info("Radio already disabled")
                return ActionResult.ALREADY_OFF
            
            # Toggle checkbox if needed
            if is_currently_enabled != enable:
                # The checkbox has a label that intercepts clicks, so we'll click the label instead
                # or use JavaScript to click the checkbox directly
                try:
                    # Try clicking the label first (more reliable)
                    label = self.driver.find_element(By.CSS_SELECTOR, "label[for='enable_ap']")
                    label.click()
                    self.logger.info(f"Radio checkbox {'enabled' if enable else 'disabled'} (clicked label)")
                except:
                    # Fallback: use JavaScript to click the checkbox directly
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    self.logger.info(f"Radio checkbox {'enabled' if enable else 'disabled'} (used JavaScript)")
                time.sleep(1)
            
            # Apply changes - look for Apply button
            apply_selectors = [
                "#apply",
                "input[value='Apply']",
                "input[type='submit'][value*='Apply']",
                "button[value*='Apply']"
            ]
            
            apply_button = None
            for selector in apply_selectors:
                try:
                    apply_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.logger.debug(f"Found Apply button using: {selector}")
                    break
                except:
                    continue
            
            if not apply_button:
                raise Exception("Could not find Apply button")
            
            apply_button.click()
            self.logger.info("Apply button clicked, waiting for changes to take effect")
            time.sleep(5)  # Wait for changes to take effect
            
            result = ActionResult.SUCCESS
            if self.config.enable_notifications:
                action = "enabled" if enable else "disabled"
                send_notification(
                    "Router Radio Controller", 
                    f"2.4GHz radio {action} successfully"
                )
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to toggle radio: {e}")
            if self.config.debug_mode:
                import traceback
                self.logger.debug(f"Toggle traceback: {traceback.format_exc()}")
                # Save page source for debugging
                try:
                    with open('/tmp/toggle_debug.html', 'w') as f:
                        f.write(self.driver.page_source)
                    self.logger.info("DEBUG: Toggle page source saved to /tmp/toggle_debug.html")
                except:
                    pass
            return ActionResult.UNEXPECTED_FAILURE
    
    def check_radio_status(self) -> RadioStatus:
        """Check current radio status"""
        self.logger.info("Checking 2.4GHz radio status")
        
        if not self._ensure_network_connection():
            return RadioStatus.NOT_CONNECTED_TO_ROUTER
        
        try:
            self._initialize_driver()
            
            if not self._login_to_router():
                return RadioStatus.UNEXPECTED_FAILURE
            
            if not self._navigate_to_advanced_settings():
                return RadioStatus.UNEXPECTED_FAILURE
            
            return self._get_radio_status_from_ui()
            
        except Exception as e:
            self.logger.error(f"Unexpected error checking radio status: {e}")
            return RadioStatus.UNEXPECTED_FAILURE
    
    def turn_on_radio(self) -> ActionResult:
        """Turn on 2.4GHz radio"""
        self.logger.info("Turning on 2.4GHz radio")
        
        if not self._ensure_network_connection():
            return ActionResult.NOT_CONNECTED_TO_ROUTER
        
        try:
            self._initialize_driver()
            
            if not self._login_to_router():
                return ActionResult.UNEXPECTED_FAILURE
            
            if not self._navigate_to_advanced_settings():
                return ActionResult.UNEXPECTED_FAILURE
            
            return self._toggle_radio(enable=True)
            
        except Exception as e:
            self.logger.error(f"Unexpected error turning on radio: {e}")
            return ActionResult.UNEXPECTED_FAILURE
    
    def turn_off_radio(self) -> ActionResult:
        """Turn off 2.4GHz radio"""
        self.logger.info("Turning off 2.4GHz radio")
        
        if not self._ensure_network_connection():
            return ActionResult.NOT_CONNECTED_TO_ROUTER
        
        try:
            self._initialize_driver()
            
            if not self._login_to_router():
                return ActionResult.UNEXPECTED_FAILURE
            
            if not self._navigate_to_advanced_settings():
                return ActionResult.UNEXPECTED_FAILURE
            
            return self._toggle_radio(enable=False)
            
        except Exception as e:
            self.logger.error(f"Unexpected error turning off radio: {e}")
            return ActionResult.UNEXPECTED_FAILURE


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Router 2.4GHz Radio Controller - Elegant automation for Netgear router radio management",
        epilog="""
Examples:
  python router_controller.py status              Check radio status
  python router_controller.py on                  Turn radio on
  python router_controller.py off                 Turn radio off
  python router_controller.py on --headless       Turn on in background
  python router_controller.py status --notifications  Enable notifications
  python router_controller.py on --config ~/my_config.yaml  Use custom config

Configuration:
  Copy config.example.yaml to ~/.router_controller_config.yaml to customize settings.
  Credentials are stored securely in macOS Keychain.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("action", choices=["status", "on", "off"], 
                       help="Action to perform: check status, turn radio on, or turn radio off")
    parser.add_argument("--headless", action="store_true",
                       help="Run browser in headless mode (no GUI, good for automation)")
    parser.add_argument("--config", type=str, metavar="PATH",
                       help="Path to custom YAML configuration file")
    parser.add_argument("--notifications", action="store_true",
                       help="Enable macOS notifications for status changes")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode (keeps browser open on failure)")
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        from pathlib import Path
        config = RouterConfig.from_yaml(Path(args.config))
    else:
        config = RouterConfig.from_yaml()
    
    # Override config with CLI arguments
    if args.headless:
        config.headless = True
    if args.notifications:
        config.enable_notifications = True
    if args.debug:
        config.debug_mode = True
    
    with RouterController(config) as controller:
        if args.action == "status":
            result = controller.check_radio_status()
            print(f"Radio Status: {result.value}")
        elif args.action == "on":
            result = controller.turn_on_radio()
            print(f"Turn On Result: {result.value}")
        elif args.action == "off":
            result = controller.turn_off_radio()
            print(f"Turn Off Result: {result.value}")


if __name__ == "__main__":
    main()
