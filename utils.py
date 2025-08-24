"""
Utility functions and decorators for router controller.
"""

import time
import functools
from typing import Callable, Any, TypeVar
import subprocess


F = TypeVar('F', bound=Callable[..., Any])


def retry(tries: int = 3, delay: int = 2, backoff: float = 1.5):
    """
    Retry decorator for handling transient failures.
    
    Args:
        tries: Number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Multiplier for delay after each failure
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= tries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == tries:
                        raise e
                    
                    if hasattr(args[0], 'logger'):
                        args[0].logger.warning(
                            f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s..."
                        )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
            return func(*args, **kwargs)
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