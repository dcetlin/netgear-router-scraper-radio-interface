"""Chrome WebDriver management for router controller"""

from typing import Optional, TYPE_CHECKING
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

if TYPE_CHECKING:
    from .logger import Logger


class WebDriverManager:
    """Chrome WebDriver management"""
    
    def __init__(self, logger: 'Logger', headless: bool = False, debug_mode: bool = False):
        self.logger = logger
        self.headless = headless
        self.debug_mode = debug_mode
        self.driver: Optional[webdriver.Chrome] = None
    
    def create_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome driver"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280,720')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        if self.headless:
            options.add_argument('--headless')
            self.logger.info("Running in headless mode")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.logger.info("Chrome driver initialized")
            return self.driver
        except Exception as e:
            self.logger.error(f"Failed to create Chrome driver: {e}")
            raise
    
    def cleanup(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                if self.debug_mode:
                    self.logger.info("Debug mode: Browser window will stay open for inspection...")
                    try:
                        input("Press Enter to close browser and continue...")
                    except (EOFError, KeyboardInterrupt):
                        self.logger.info("Debug mode interrupted, closing browser...")
                self.driver.quit()
                self.logger.debug("WebDriver cleaned up")
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")