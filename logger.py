"""Logging system for router controller"""

import logging
import sys
import time
import threading
from pathlib import Path


class Logger:
    """Dynamic single-line logging system with counter"""
    
    def __init__(self, name: str = "RouterController", dynamic: bool = True):
        self.logger = logging.getLogger(name)
        self.dynamic = dynamic
        self.counter = 0
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with file output only for dynamic mode"""
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # File handler for persistent logging
            log_file = Path.home() / ".router_controller.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Formatter for file
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Only add console handler if not in dynamic mode
            if not self.dynamic:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)
    
    def _dynamic_log(self, message: str, level: str = "INFO"):
        """Display single dynamic log line with counter"""
        if not self.dynamic:
            return
            
        self.counter += 1
        
        # Clear line and show new message with counter
        sys.stdout.write(f"\r\033[K[{self.counter}] {message}")
        sys.stdout.flush()
    
    def _start_continuous_counter(self, message: str):
        """Start a continuous counter for long operations"""
        if not self.dynamic:
            return None
            
        self.counter += 1
        start_time = time.time()
        
        def update_counter():
            while not self._stop_counter.is_set():
                elapsed = int(time.time() - start_time)
                sys.stdout.write(f"\r\033[K[{self.counter}] {message} ({elapsed}s)")
                sys.stdout.flush()
                time.sleep(1)
        
        self._stop_counter = threading.Event()
        counter_thread = threading.Thread(target=update_counter, daemon=True)
        counter_thread.start()
        
        return self._stop_counter
    
    def info(self, message: str):
        self.logger.info(message)
        self._dynamic_log(message, "INFO")
    
    def error(self, message: str):
        self.logger.error(message)
        self._dynamic_log(f"❌ {message}", "ERROR")
    
    def debug(self, message: str):
        self.logger.debug(message)
        if self.dynamic:
            self._dynamic_log(f"🔍 {message}", "DEBUG")
    
    def warning(self, message: str):
        self.logger.warning(message)
        self._dynamic_log(f"⚠️  {message}", "WARNING")
    
    def clear_line(self):
        """Clear the current dynamic log line"""
        if self.dynamic:
            sys.stdout.write(f"\r\033[K")
            sys.stdout.flush()
    
