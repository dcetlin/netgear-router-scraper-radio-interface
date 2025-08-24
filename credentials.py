"""Secure credential management using macOS keychain"""

from typing import Tuple, Optional, TYPE_CHECKING
import keyring

if TYPE_CHECKING:
    from .logger import Logger


class CredentialManager:
    """Secure credential storage and retrieval"""
    
    def __init__(self, logger: 'Logger', service_name: str):
        self.logger = logger
        self.service_name = service_name
    
    def get_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """Retrieve stored credentials"""
        try:
            username = keyring.get_password(self.service_name, "username")
            password = keyring.get_password(self.service_name, "password")
            
            if not username or not password:
                self.logger.info("No stored credentials found")
                return None, None
            
            return username, password
        except Exception as e:
            self.logger.error(f"Failed to retrieve credentials: {e}")
            return None, None
    
    def store_credentials(self, username: str, password: str) -> bool:
        """Store credentials securely"""
        try:
            keyring.set_password(self.service_name, "username", username)
            keyring.set_password(self.service_name, "password", password)
            self.logger.info("Credentials stored successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store credentials: {e}")
            return False
    
    def prompt_for_credentials(self) -> Tuple[str, str]:
        """Prompt user for credentials"""
        print("\nRouter admin credentials not found.")
        print("These will be stored securely in macOS keychain (viewable in Passwords app).")
        username = input("Enter admin username: ").strip()
        password = input("Enter admin password: ").strip()
        
        if input("Store credentials securely in keychain? (y/N): ").lower().startswith('y'):
            self.store_credentials(username, password)
            print("Credentials stored. You can manage them in the Passwords app if needed.")
        
        return username, password