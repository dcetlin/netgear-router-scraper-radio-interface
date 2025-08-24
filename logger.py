"""
Elegant logging system for router controller.
"""

import logging
from pathlib import Path


class Logger:
    """Simple, elegant logging system"""
    
    def __init__(self, name: str = "RouterController"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with console and file output"""
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # File handler
            log_file = Path.home() / ".router_controller.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str): self.logger.info(message)
    def error(self, message: str): self.logger.error(message)
    def debug(self, message: str): self.logger.debug(message)
    def warning(self, message: str): self.logger.warning(message)