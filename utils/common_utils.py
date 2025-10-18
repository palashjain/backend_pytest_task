import json
import re
from typing import Any, Dict, Callable, TypeVar
from utils.base_utils import BaseClassUtils

T = TypeVar('T')


class CommonUtils(BaseClassUtils):

    @staticmethod
    def log_and_raise(func: Callable[..., T], *args, **kwargs) -> T:
        return CommonUtils.safe_execute(func, *args, **kwargs)

    @staticmethod
    def deep_copy_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        return json.loads(json.dumps(data))

    @staticmethod
    def merge_dicts(base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> Dict[str, Any]:
        merged = base_dict.copy()
        for key, value in override_dict.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = CommonUtils.merge_dicts(merged[key], value)
            else:
                merged[key] = value
        return merged

    @staticmethod
    def get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
        try:
            keys = re.split(r'[\.\[\]]+', path)
            keys = [k for k in keys if k]
            
            current = data
            
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    index = int(key)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return default
                else:
                    return default
                
                if current is None:
                    return default
            
            return current
        except Exception:
            return default

    @staticmethod
    def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
        try:
            keys = re.split(r'[\.\[\]]+', path)
            keys = [k for k in keys if k]
            
            current = data
            
            for key in keys[:-1]:
                current = CommonUtils._ensure_nested_structure(current, key)
            
            final_key = keys[-1]
            CommonUtils._set_final_value(current, final_key, value)
        except Exception as e:
            CommonUtils.get_logger().error(f"Error setting nested value at {path}: {str(e)}")

    @staticmethod
    def _ensure_nested_structure(current: Any, key: str) -> Any:
        if key.isdigit():
            index = int(key)
            if not isinstance(current, list):
                current = []
            while len(current) <= index:
                current.append({})
            return current[index]
        else:
            if not isinstance(current, dict):
                current = {}
            if key not in current:
                current[key] = {}
            return current[key]

    @staticmethod
    def _set_final_value(current: Any, key: str, value: Any) -> None:
        if key.isdigit():
            index = int(key)
            if not isinstance(current, list):
                current = []
            while len(current) <= index:
                current.append(None)
            current[index] = value
        else:
            if not isinstance(current, dict):
                current = {}
            current[key] = value
