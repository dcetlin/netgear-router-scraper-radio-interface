"""Data models and enums for router radio controller"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


class RadioStatus(Enum):
    RADIO_ON = "RADIO_ON"
    RADIO_OFF = "RADIO_OFF"
    NOT_CONNECTED_TO_ROUTER = "NOT_CONNECTED_TO_ROUTER"
    VPN_CONNECTED = "VPN_CONNECTED"
    UNEXPECTED_FAILURE = "UNEXPECTED_FAILURE"


class ActionResult(Enum):
    SUCCESS = "SUCCESS"
    ALREADY_ON = "ALREADY_ON"
    ALREADY_OFF = "ALREADY_OFF"
    NOT_CONNECTED_TO_ROUTER = "NOT_CONNECTED_TO_ROUTER"
    VPN_CONNECTED = "VPN_CONNECTED"
    UNEXPECTED_FAILURE = "UNEXPECTED_FAILURE"


@dataclass
class RouterConfig:
    """Configuration for router connection"""
    target_network: str = "1_lemonlemon_1"
    router_url: str = "https://routerlogin.net/"
    timeout: int = 10
    service_name: str = "router_admin"
    headless: bool = False
    enable_notifications: bool = False
    debug_mode: bool = False
    
    @classmethod
    def from_yaml(cls, config_path: Optional[Path] = None) -> 'RouterConfig':
        """Load configuration from YAML file with validation"""
        if config_path is None:
            config_path = Path.home() / ".router_controller_config.yaml"
        
        if not config_path.exists():
            return cls()
        
        try:
            import yaml
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Validate configuration values
            validated_data = {}
            for k, v in data.items():
                if hasattr(cls, k):
                    if k == 'timeout' and (not isinstance(v, int) or v < 1):
                        print(f"⚠️  Invalid timeout value '{v}', using default: 10")
                        continue
                    if k in ['headless', 'enable_notifications', 'debug_mode'] and not isinstance(v, bool):
                        print(f"⚠️  Invalid boolean value for '{k}': {v}, using default")
                        continue
                    validated_data[k] = v
                else:
                    print(f"⚠️  Unknown configuration key '{k}' ignored")
            
            return cls(**validated_data)
        except ImportError:
            print("⚠️  PyYAML not installed, using default configuration")
            return cls()
        except Exception as e:
            print(f"⚠️  Error loading config file: {e}, using default configuration")
            return cls()
    
    def to_yaml(self, config_path: Optional[Path] = None) -> bool:
        """Save configuration to YAML file"""
        if config_path is None:
            config_path = Path.home() / ".router_controller_config.yaml"
        
        try:
            import yaml
            config_dict = {
                'target_network': self.target_network,
                'router_url': self.router_url,
                'timeout': self.timeout,
                'service_name': self.service_name,
                'headless': self.headless,
                'enable_notifications': self.enable_notifications,
                'debug_mode': self.debug_mode
            }
            with open(config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
            return True
        except ImportError:
            return False
        except Exception:
            return False