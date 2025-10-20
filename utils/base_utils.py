import logging
from typing import Any, Callable, TypeVar
from utils.logger_utils import LoggerUtils

T = TypeVar('T')


class BaseClassUtils:
    _logger: logging.Logger = None
    
    @classmethod
    def get_logger(cls) -> logging.Logger:
        if cls._logger is None:
            cls._logger = LoggerUtils.get_logger(cls.__name__)
        return cls._logger
    
    @classmethod
    def safe_execute(cls, func: Callable[..., T], *args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            cls.get_logger().error(f"Error executing {func.__name__}: {str(e)}")
            raise
