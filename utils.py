"""Notifications and output formatting for router controller"""

import subprocess


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