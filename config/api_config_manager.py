import json
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger_utils import LoggerUtils


class APIConfigManager:
    _instance: Optional['APIConfigManager'] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls) -> 'APIConfigManager':
        if cls._instance is None:
            cls._instance = super(APIConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._config is None:
            self._logger = LoggerUtils.get_logger(__name__)
            self._load_config()

    def _load_config(self) -> None:
        try:
            config_path = Path(__file__).parent / "api_config.json"
            with open(config_path, 'r', encoding='utf-8') as file:
                self._config = json.load(file)
            self._logger.info("API configuration loaded successfully")
        except Exception as e:
            self._logger.error(f"Error loading API configuration: {str(e)}")
            raise

    def get_base_data_file(self, api_name: str) -> str:
        api_config = self._get_api_config(api_name)
        return api_config["base_data_file"]

    def get_schema_file(self, api_name: str) -> str:
        api_config = self._get_api_config(api_name)
        return api_config["schema_file"]

    def _get_api_config(self, api_name: str) -> Dict[str, Any]:
        if api_name not in self._config["apis"]:
            raise ValueError(f"API '{api_name}' not found in configuration")
        return self._config["apis"][api_name]
