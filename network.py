"""Network connectivity verification for router controller"""

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import Logger


class NetworkChecker:
    """Network connectivity verification"""
    
    def __init__(self, logger: 'Logger', target_network: str):
        self.logger = logger
        self.target_network = target_network
    
    def is_vpn_connected(self) -> bool:
        """Check if VPN is currently connected"""
        try:
            result = subprocess.run([
                'scutil', '--nc', 'list'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                vpn_connected = 'Connected' in result.stdout
                if vpn_connected:
                    self.logger.warning("VPN connection detected - please disconnect VPN and try again")
                else:
                    self.logger.debug("No VPN connection detected")
                return vpn_connected
            else:
                self.logger.debug("Could not check VPN status")
                return False
        except Exception as e:
            self.logger.debug(f"VPN check failed: {e}")
            return False
    
    def is_connected_to_target_network(self) -> bool:
        """Check if connected to target WiFi network or wired connection"""
        try:
            # Check WiFi connection on macOS (try common WiFi interfaces)
            wifi_interfaces = ['en0', 'en1']
            for interface in wifi_interfaces:
                try:
                    wifi_result = subprocess.run([
                        'networksetup', '-getairportnetwork', interface
                    ], capture_output=True, text=True)
                    
                    if wifi_result.returncode == 0:
                        current_network = wifi_result.stdout.strip()
                        if self.target_network in current_network:
                            self.logger.info(f"Connected to target WiFi on {interface}: {current_network}")
                            return True
                except:
                    continue
            
            # Check all ethernet interfaces for wired connection
            # Get list of all network interfaces
            ifconfig_result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            if ifconfig_result.returncode != 0:
                self.logger.warning("Failed to get network interface list")
                return False
            
            # Parse interfaces and check each ethernet interface
            interfaces = []
            lines = ifconfig_result.stdout.split('\n')
            for line in lines:
                if line and not line.startswith('\t') and not line.startswith(' '):
                    interface_name = line.split(':')[0]
                    if interface_name.startswith('en'):  # Ethernet interfaces
                        interfaces.append(interface_name)
            
            self.logger.debug(f"Found ethernet interfaces: {interfaces}")
            
            for interface in interfaces:
                try:
                    wired_result = subprocess.run([
                        'ifconfig', interface
                    ], capture_output=True, text=True)
                    
                    if wired_result.returncode == 0:
                        output = wired_result.stdout
                        # Check if interface is active and has an IP
                        if ("status: active" in output and "inet " in output) or \
                           ("flags=" in output and "UP" in output and "inet " in output):
                            # Extract IP to verify it's in router subnet
                            for line in output.split('\n'):
                                if 'inet ' in line and not '127.0.0.1' in line:
                                    ip_info = line.strip()
                                    self.logger.info(f"Connected via wired ethernet on {interface}: {ip_info}")
                                    return True
                except:
                    continue
            
            self.logger.warning("Not connected to target network or wired connection")
            return False
            
        except Exception as e:
            self.logger.error(f"Network check failed: {e}")
            return False