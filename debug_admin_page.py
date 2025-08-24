#!/usr/bin/env python3
"""
Debug script to inspect the router admin page structure for radio status
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def debug_admin_page():
    """Debug the router admin page to see actual structure for radio status"""
    
    # Setup Chrome driver (non-headless for debugging)
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,720')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("🔍 Starting router admin page inspection...")
        
        # Navigate to router
        print("📡 Navigating to https://routerlogin.net/")
        driver.get("https://routerlogin.net/")
        time.sleep(2)
        
        # Handle SSL warning
        if "Your connection is not private" in driver.page_source:
            print("🛡️ SSL warning detected, bypassing...")
            try:
                advanced_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "details-button"))
                )
                advanced_button.click()
                time.sleep(1)
                
                proceed_link = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "proceed-link"))
                )
                proceed_link.click()
                time.sleep(3)
                print("✅ SSL warning bypassed")
            except Exception as e:
                print(f"❌ SSL bypass failed: {e}")
                return
        
        # Auto-login using stored credentials
        print("\n🔑 Attempting automatic login...")
        try:
            from credentials import CredentialManager
            from logger import Logger
            
            logger = Logger()
            credential_manager = CredentialManager(logger, "router_admin")
            username, password = credential_manager.get_credentials()
            
            if not username or not password:
                print("❌ No stored credentials found. Please run the main script first to store credentials.")
                return
            
            # Wait for and fill login form
            wait = WebDriverWait(driver, 10)
            username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            password_field = driver.find_element(By.NAME, "password")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # Submit login
            login_button = driver.find_element(By.CSS_SELECTOR, "a[onclick*='login']")
            login_button.click()
            
            print("✅ Login submitted, waiting for page load...")
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Auto-login failed: {e}")
            print("Please ensure you have stored credentials by running the main script first")
            return
        
        # Navigate to admin page
        print("\n📡 Navigating to admin page...")
        driver.get("https://routerlogin.net/adv_index.htm")
        time.sleep(3)
        
        print(f"📄 Current URL: {driver.current_url}")
        print(f"📑 Page title: {driver.title}")
        
        # Look for Advanced Setup button
        print("\n🔍 Looking for Advanced Setup elements...")
        advanced_selectors = [
            '#advanced_bt',
            'button[id*="advanced"]',
            '*[onclick*="advanced"]',
            '*[id*="advanced"]'
        ]
        
        for selector in advanced_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"📂 Advanced Setup found: {selector} ({len(elements)} elements)")
                    for i, elem in enumerate(elements):
                        print(f"   Element {i}: tag='{elem.tag_name}', text='{elem.text}', id='{elem.get_attribute('id')}', class='{elem.get_attribute('class')}'")
                    
                    # Try clicking the first one
                    print(f"🖱️ Clicking Advanced Setup...")
                    elements[0].click()
                    time.sleep(2)
                    break
            except Exception as e:
                pass
        
        # Look for wireless settings elements
        print("\n🔍 Looking for Wireless Settings elements...")
        wireless_selectors = [
            '*[text()*="Wireless Settings"]',
            '*[contains(text(), "2.4GHz")]',
            '*[contains(text(), "Wireless")]',
            '#wladv',
            '*[id*="wireless"]',
            '*[id*="wl"]',
            'div[class*="wireless"]',
            'span[class*="wireless"]'
        ]
        
        # Also search in page source
        page_source = driver.page_source
        wireless_terms = ["Wireless Settings", "2.4GHz", "wireless", "radio", "WiFi", "wifi"]
        
        print("🔍 Searching page source for wireless-related terms...")
        for term in wireless_terms:
            if term.lower() in page_source.lower():
                print(f"✅ Found '{term}' in page source")
        
        # Look for status indicators
        print("\n🔍 Looking for status indicator elements...")
        status_selectors = [
            '*[class*="status"]',
            '*[class*="img_status"]',
            'img[class*="status"]',
            'div[class*="status"]',
            '*[class*="good"]',
            '*[class*="warning"]',
            '*[class*="error"]'
        ]
        
        for selector in status_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"📊 Status elements found: {selector} ({len(elements)} elements)")
                    for i, elem in enumerate(elements[:5]):  # Limit to first 5
                        print(f"   Element {i}: tag='{elem.tag_name}', class='{elem.get_attribute('class')}', text='{elem.text}', id='{elem.get_attribute('id')}'")
            except Exception as e:
                pass
        
        # Save page source for inspection
        with open('/Users/dzc/Documents/router-radio-toggle/debug_admin_page.html', 'w') as f:
            f.write(driver.page_source)
        print("\n💾 Admin page source saved to: debug_admin_page.html")
        
        # Get page structure overview
        print("\n📋 Page structure overview:")
        main_divs = driver.find_elements(By.TAG_NAME, "div")[:10]  # First 10 divs
        for i, div in enumerate(main_divs):
            div_id = div.get_attribute('id') or 'no-id'
            div_class = div.get_attribute('class') or 'no-class'
            div_text = (div.text or '').strip()[:50]  # First 50 chars
            print(f"   Div {i}: id='{div_id}', class='{div_class}', text='{div_text}...'")
        
        print(f"\n⏸️  Browser window will stay open for 60 seconds for manual inspection...")
        print("   Check the browser window to see the actual admin page structure")
        print("   Look for wireless settings and status indicators")
        time.sleep(60)
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("🏁 Debugging complete")

if __name__ == "__main__":
    debug_admin_page()