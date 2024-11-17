"""Configuration management utilities."""

import json
from pathlib import Path
import os
from typing import Dict, Any, Optional

# Constants
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    'app_name': 'AutoLife',
    'version': '1.0.0',
    'debug': False,
    'paths': {
        'media': '',
        'subtitles': '',
        'output': '',
        'cache': ''
    },
    'processing': {
        'threads': 4,
        'gpu_enabled': True,
        'batch_size': 32
    },
    'ui': {
        'theme': 'light',
        'language': 'en',
        'font_size': 12
    }
}

class Config:
    """Configuration manager class."""
    
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        """Initialize configuration with optional data.
        
        Args:
            data (Dict[str, Any], optional): Initial configuration data
        """
        self.data = data if data is not None else DEFAULT_CONFIG.copy()
        self._validate()
    
    def _validate(self):
        """Validate configuration data."""
        # Validate paths
        paths = self.data.get('paths', {})
        for key, path in paths.items():
            if path and not isinstance(path, (str, Path)):
                raise ValueError(f"Invalid path for {key}: {path}")
        
        # Validate processing settings
        processing = self.data.get('processing', {})
        threads = processing.get('threads', 0)
        if not isinstance(threads, int) or threads < 0:
            raise ValueError(f"Invalid thread count: {threads}")
        
        batch_size = processing.get('batch_size', 0)
        if not isinstance(batch_size, int) or batch_size < 1:
            raise ValueError(f"Invalid batch size: {batch_size}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key (str): Configuration key (supports dot notation)
            default (Any): Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        parts = key.split('.')
        value = self.data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, default)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value.
        
        Args:
            key (str): Configuration key (supports dot notation)
            value (Any): Value to set
        """
        parts = key.split('.')
        target = self.data
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value
        self._validate()

def load_config(config_file: Path) -> Config:
    """Load configuration from file.
    
    Args:
        config_file (Path): Path to configuration file
        
    Returns:
        Config: Configuration instance
        
    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file is invalid JSON
    """
    config_file = Path(config_file)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        data = json.load(f)
    
    return Config(data)

def save_config(config: Config, config_file: Path):
    """Save configuration to file.
    
    Args:
        config (Config): Configuration instance
        config_file (Path): Path to save configuration
    """
    config_file = Path(config_file)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config.data, f, indent=4)

def get_config(config_file: Path) -> Config:
    """Get or create configuration instance.
    
    Args:
        config_file (Path): Path to configuration file
        
    Returns:
        Config: Configuration instance
    """
    try:
        return load_config(config_file)
    except FileNotFoundError:
        config = Config()
        save_config(config, config_file)
        return config

def update_config(config: Config, updates: Dict[str, Any]):
    """Update configuration with new values.
    
    Args:
        config (Config): Configuration instance
        updates (Dict[str, Any]): Updates to apply
    """
    for key, value in updates.items():
        config.set(key, value)
