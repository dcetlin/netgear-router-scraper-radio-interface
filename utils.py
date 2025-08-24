"""Utility functions and decorators for router controller"""

import time
import functools
from typing import Callable, Any, TypeVar
import subprocess


F = TypeVar('F', bound=Callable[..., Any])


def retry(tries: int = 3, delay: int = 2, backoff: float = 1.5, exceptions: tuple = (Exception,)):
    """
    Enhanced retry decorator with exponential backoff and selective exception handling.
    
    Args:
        tries: Number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Multiplier for delay after each failure
        exceptions: Tuple of exceptions to retry on (default: all exceptions)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            last_exception = None
            
            while attempt <= tries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == tries:
                        raise e
                    
                    if hasattr(args[0], 'logger'):
                        args[0].logger.warning(
                            f"Attempt {attempt}/{tries} failed: {type(e).__name__}: {e}"
                        )
                        # Show retry progress with spinner if available
                        if hasattr(args[0].logger, 'progress_spinner'):
                            spinner = args[0].logger.progress_spinner(
                                f"Retrying in {current_delay}s... (attempt {attempt + 1}/{tries})"
                            )
                            time.sleep(current_delay)
                            spinner.set()
                        else:
                            time.sleep(current_delay)
                    else:
                        time.sleep(current_delay)
                    
                    current_delay *= backoff
                    attempt += 1
                except Exception as e:
                    # Don't retry on unexpected exceptions
                    raise e
            
            # This should never be reached, but just in case
            raise last_exception or Exception("Retry logic failed unexpectedly")
        return wrapper
    return decorator


def send_notification(title: str, message: str, sound: bool = True) -> bool:
    """
    Send macOS notification using osascript.
    
    Args:
        title: Notification title
        message: Notification message
        sound: Whether to play sound
    
    Returns:
        True if notification sent successfully
    """
    try:
        sound_param = "with sound name \"default\"" if sound else ""
        script = f'''
        display notification "{message}" with title "{title}" {sound_param}
        '''
        
        result = subprocess.run([
            'osascript', '-e', script
        ], capture_output=True, text=True)
        
        return result.returncode == 0
    except Exception:
        return False


def format_status_output(status_value: str, action_type: str = "status") -> str:
    """
    Format status output with colors and emojis for maximum clarity.
    
    Args:
        status_value: The status/result value
        action_type: Type of action (status, on, off)
    
    Returns:
        Formatted colored string with emoji
    """
    # ANSI color codes
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    status_map = {
        # Status results
        'RADIO_ON': (f'🟢 {GREEN}{BOLD}RADIO ON{RESET}', 'Radio is currently enabled'),
        'RADIO_OFF': (f'🔴 {RED}{BOLD}RADIO OFF{RESET}', 'Radio is currently disabled'),
        
        # Action results
        'SUCCESS': (f'✅ {GREEN}{BOLD}SUCCESS{RESET}', 'Operation completed successfully'),
        'ALREADY_ON': (f'🔵 {BLUE}{BOLD}ALREADY ON{RESET}', 'Radio was already enabled'),
        'ALREADY_OFF': (f'🔵 {BLUE}{BOLD}ALREADY OFF{RESET}', 'Radio was already disabled'),
        
        # Error conditions
        'NOT_CONNECTED_TO_ROUTER': (f'📡 {YELLOW}{BOLD}NOT CONNECTED{RESET}', 'Please connect to router network'),
        'VPN_CONNECTED': (f'🔒 {YELLOW}{BOLD}VPN DETECTED{RESET}', 'Please disconnect VPN and try again'),
        'UNEXPECTED_FAILURE': (f'❌ {RED}{BOLD}FAILED{RESET}', 'An unexpected error occurred'),
    }
    
    emoji_status, description = status_map.get(status_value, (f'❓ {BOLD}UNKNOWN{RESET}', 'Unknown status'))
    
    return f"\n{emoji_status}\n{description}\n"