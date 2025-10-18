import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from config.configmanager import ConfigManager


class LoggerUtils:
    _logger: Optional[logging.Logger] = None
    _request_logger: Optional[logging.Logger] = None
    _response_logger: Optional[logging.Logger] = None
    _config_manager = ConfigManager()
    _session_log_file: Optional[str] = None
    _session_request_log_file: Optional[str] = None
    _session_response_log_file: Optional[str] = None
    
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def initialize_session_logging(cls) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = Path(cls._config_manager.log_file).parent
        
        cls._session_log_file = str(log_dir / f"test_execution_{timestamp}.log")
        cls._session_request_log_file = str(log_dir / f"api_requests_{timestamp}.log")
        cls._session_response_log_file = str(log_dir / f"api_responses_{timestamp}.log")
        
        cls._logger = None
        cls._request_logger = None
        cls._response_logger = None
        
        return cls._session_log_file

    @classmethod
    def get_logger(cls, name: str = __name__) -> logging.Logger:
        if cls._logger is None:
            cls._setup_logger(name)
        return cls._logger

    @classmethod
    def get_request_logger(cls, name: str = __name__) -> logging.Logger:
        if cls._request_logger is None:
            cls._setup_request_logger(name)
        return cls._request_logger

    @classmethod
    def get_response_logger(cls, name: str = __name__) -> logging.Logger:
        if cls._response_logger is None:
            cls._setup_response_logger(name)
        return cls._response_logger

    @classmethod
    def _setup_logger(cls, name: str) -> None:
        cls._logger = logging.getLogger(name)
        cls._logger.setLevel(getattr(logging, cls._config_manager.log_level))

        cls._logger.handlers.clear()

        try:
            log_format = cls._config_manager.get("LOGGING", "log_format")
        except Exception:
            log_format = cls.DEFAULT_LOG_FORMAT
        
        formatter = logging.Formatter(log_format)

        log_file_path = cls._session_log_file if cls._session_log_file else cls._config_manager.log_file
        log_file_path = Path(log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        cls._logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        cls._logger.addHandler(console_handler)

    @classmethod
    def _setup_request_logger(cls, name: str) -> None:
        cls._request_logger = logging.getLogger(f"{name}.requests")
        cls._request_logger.setLevel(logging.DEBUG)

        cls._request_logger.handlers.clear()

        try:
            log_format = cls._config_manager.get("LOGGING", "log_format")
        except Exception:
            log_format = cls.DEFAULT_LOG_FORMAT
        
        formatter = logging.Formatter(log_format)

        log_file_path = cls._session_request_log_file if cls._session_request_log_file else "logs/api_requests.log"
        log_file_path = Path(log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        cls._request_logger.addHandler(file_handler)

    @classmethod
    def _setup_response_logger(cls, name: str) -> None:
        cls._response_logger = logging.getLogger(f"{name}.responses")
        cls._response_logger.setLevel(logging.DEBUG)

        cls._response_logger.handlers.clear()

        try:
            log_format = cls._config_manager.get("LOGGING", "log_format")
        except Exception:
            log_format = cls.DEFAULT_LOG_FORMAT
        
        formatter = logging.Formatter(log_format)

        log_file_path = cls._session_response_log_file if cls._session_response_log_file else "logs/api_responses.log"
        log_file_path = Path(log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        cls._response_logger.addHandler(file_handler)

    @classmethod
    def log_test_start(cls, test_name: str) -> None:
        cls.get_logger().info(f"=== Starting Test: {test_name} ===")

    @classmethod
    def log_test_end(cls, test_name: str, status: str) -> None:
        cls.get_logger().info(f"=== Test {test_name} {status} ===")

    @classmethod
    def log_api_request(cls, method: str, url: str, headers: dict = None, data: dict = None) -> None:
        logger = cls.get_logger()
        logger.info(f"API Request: {method} {url}")
        if headers:
            logger.debug(f"Headers: {headers}")
        if data:
            logger.debug(f"Request Data: {data}")
        
        request_logger = cls.get_request_logger()
        request_logger.info("=== API REQUEST ===")
        request_logger.info(f"Method: {method}")
        request_logger.info(f"URL: {url}")
        if headers:
            request_logger.info(f"Headers: {headers}")
        if data:
            request_logger.info(f"Request Data: {data}")
        request_logger.info(f"Timestamp: {datetime.now().isoformat()}")

    @classmethod
    def log_api_response(cls, status_code: int, response_data: dict = None, response_time: float = None) -> None:
        logger = cls.get_logger()
        logger.info(f"API Response: Status Code {status_code}")
        if response_time:
            logger.info(f"Response Time: {response_time:.2f}s")
        if response_data:
            logger.debug(f"Response Data: {response_data}")
        
        response_logger = cls.get_response_logger()
        response_logger.info("=== API RESPONSE ===")
        response_logger.info(f"Status Code: {status_code}")
        if response_time:
            response_logger.info(f"Response Time: {response_time:.2f}s")
        if response_data:
            response_logger.info(f"Response Data: {response_data}")
        response_logger.info(f"Timestamp: {datetime.now().isoformat()}")

    @classmethod
    def log_error(cls, error: Exception, context: str = "") -> None:
        logger = cls.get_logger()
        logger.error(f"Error in {context}: {str(error)}", exc_info=True)
