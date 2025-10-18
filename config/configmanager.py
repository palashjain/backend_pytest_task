"""
Configuration Manager - Singleton pattern for managing application configuration
"""
import configparser
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """
    Singleton Configuration Manager for handling application settings
    """
    _instance: Optional['ConfigManager'] = None
    _config: Optional[configparser.ConfigParser] = None

    def __new__(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._config is None:
            self._load_config()

    def _load_config(self) -> None:
        """Load configuration from config.ini file"""
        self._config = configparser.ConfigParser()
        config_path = Path(__file__).parent / "config.ini"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        self._config.read(config_path)

    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Get configuration value by section and key"""
        if self._config is None:
            self._load_config()
        return self._config.get(section, key, fallback=fallback)

    def get_section(self, section: str) -> Dict[str, str]:
        """Get entire section as dictionary"""
        if self._config is None:
            self._load_config()
        return dict(self._config.items(section))

    def get_boolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value"""
        if self._config is None:
            self._load_config()
        return self._config.getboolean(section, key, fallback=fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value"""
        if self._config is None:
            self._load_config()
        return self._config.getint(section, key, fallback=fallback)

    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value"""
        if self._config is None:
            self._load_config()
        return self._config.getfloat(section, key, fallback=fallback)

    @property
    def base_url(self) -> str:
        """Get base API URL"""
        return self.get("API", "base_url")

    @property
    def username(self) -> str:
        """Get username for authentication"""
        return self.get("CREDENTIALS", "username")

    @property
    def password(self) -> str:
        """Get password for authentication"""
        return self.get("CREDENTIALS", "password")

    @property
    def test_data_dir(self) -> str:
        """Get test data directory path"""
        return self.get("TEST_DATA", "test_data_dir")

    @property
    def log_level(self) -> str:
        """Get logging level"""
        return self.get("LOGGING", "log_level")

    @property
    def log_file(self) -> str:
        """Get log file path"""
        return self.get("LOGGING", "log_file")
