"""
Configuration loader utility
"""
import json
import os


def load_config(config_path: str = "config/settings.json") -> dict:
    """
    Load configuration from JSON file
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_config_value(config: dict, *keys, default=None):
    """
    Get a nested value from config dictionary
    
    Args:
        config: Configuration dictionary
        *keys: Keys to traverse
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    current = config
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


# Load config on module import
try:
    CONFIG = load_config()
except Exception as e:
    print(f"Error loading config: {e}")
    CONFIG = {}
