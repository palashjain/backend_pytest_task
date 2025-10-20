import json
from typing import Any, Dict, List, Optional, Union, Callable
from utils.base_utils import BaseClassUtils
from utils.common_utils import CommonUtils


class ResponseUtils(BaseClassUtils):
    
    
    @classmethod
    def _log_extraction(cls, value: Any, field_name: str, found: bool = True) -> None:
        if found and value is not None:
            cls.get_logger().debug(f"Extracted {field_name}: {value}")
        elif not found:
            cls.get_logger().warning(f"{field_name} not found in response")
    
    @classmethod
    def _extract_nested_value(cls, data: Dict[str, Any], path: str, field_name: str, default_value: Any = None) -> Any:
        try:
            value = cls._get_nested_value(data, path)
            cls._log_extraction(value, field_name, value is not None)
            return str(value) if value is not None else default_value
        except Exception as e:
            cls.get_logger().error(f"Error extracting {field_name}: {str(e)}")
            return default_value
    
    @classmethod
    def _extract_array_value(cls, data: Dict[str, Any], array_path: str, field_name: str, 
                           index: int = 0, default_value: Any = None) -> Any:
        try:
            array_data = cls._get_nested_value(data, array_path)
            if array_data and isinstance(array_data, list) and len(array_data) > index:
                value = array_data[index]
                cls._log_extraction(value, field_name, True)
                return str(value) if value is not None else default_value
            
            cls._log_extraction(None, field_name, False)
            return default_value
        except Exception as e:
            cls.get_logger().error(f"Error extracting {field_name} from array: {str(e)}")
            return default_value
    
    @classmethod
    def _extract_array_field(cls, data: Dict[str, Any], array_path: str, field_path: str, 
                           field_name: str, index: int = 0, default_value: Any = None) -> Any:
        try:
            array_data = cls._get_nested_value(data, array_path)
            if array_data and isinstance(array_data, list) and len(array_data) > index:
                element = array_data[index]
                if isinstance(element, dict):
                    value = cls._get_nested_value(element, field_path)
                    cls._log_extraction(value, field_name, value is not None)
                    return str(value) if value is not None else default_value
            
            cls._log_extraction(None, field_name, False)
            return default_value
        except Exception as e:
            cls.get_logger().error(f"Error extracting {field_name} from array field: {str(e)}")
            return default_value

    @classmethod
    def parse_json_response(cls, response_text: str) -> Dict[str, Any]:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            cls.get_logger().error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON response: {str(e)}")

    @classmethod
    def extract_cookie_from_session(cls, session_cookies) -> Optional[str]:
        try:
            if not session_cookies:
                cls.get_logger().debug("No session cookies available")
                return None
            
            cookie_parts = []
            for cookie in session_cookies:
                cookie_parts.append(f"{cookie.name}={cookie.value}")
            
            if cookie_parts:
                cookie_string = "; ".join(cookie_parts)
                cls.get_logger().debug(f"Extracted session cookie: {cookie_string[:50]}...")
                return cookie_string
            
            cls.get_logger().debug("No cookies found in session")
            return None
        except Exception as e:
            cls.get_logger().error(f"Error extracting cookie from session: {str(e)}")
            return None

    @classmethod
    def extract_workspace_id(cls, response_data: Dict[str, Any]) -> Optional[str]:
        return cls._extract_nested_value(response_data, 'user.workspace[0].urmId', 'workspace ID')

    @classmethod
    def extract_awb_number(cls, response_data: Dict[str, Any]) -> Optional[str]:
        return cls._extract_nested_value(response_data, 'data[0].awb_number', 'AWB number')

    @classmethod
    def _get_nested_value(cls, data: Dict[str, Any], path: str) -> Any:
        return CommonUtils.get_nested_value(data, path)

    @classmethod
    def validate_response_success(cls, response_data: Dict[str, Any]) -> bool:
        try:
            success = response_data.get('success', False)
            if isinstance(success, bool):
                return success
            
            if isinstance(success, str):
                return success.lower() in ['true', '1', 'yes', 'success']
            
            return False
        except Exception as e:
            cls.get_logger().error(f"Error validating response success: {str(e)}")
            return False

    @classmethod
    def get_error_message(cls, response_data: Dict[str, Any]) -> Optional[str]:
        return cls._extract_nested_value(response_data, 'failed_entries.0.message', 'error message')

    @classmethod
    def extract_trip_id(cls, response_data: Dict[str, Any]) -> Optional[str]:
        try:
            trip_ids = response_data.get('data', [])
            if trip_ids and isinstance(trip_ids, list) and len(trip_ids) > 0:
                trip_id = trip_ids[0]
                cls._log_extraction(trip_id, 'trip ID', True)
                return str(trip_id)
            
            cls._log_extraction(None, 'trip ID', False)
            return None
        except Exception as e:
            cls.get_logger().error(f"Error extracting trip ID: {str(e)}")
            return None

    @classmethod
    def extract_task_ids(cls, response_data: Dict[str, Any]) -> List[str]:
        try:
            data_array = response_data.get('data', [])
            if data_array and isinstance(data_array, list) and len(data_array) > 0:
                task_ids = data_array[0].get('task_ids', [])
                if task_ids and isinstance(task_ids, list):
                    task_id_strings = [str(task_id) for task_id in task_ids]
                    cls._log_extraction(task_id_strings, 'task IDs', True)
                    return task_id_strings
            
            cls._log_extraction(None, 'task IDs', False)
            return []
        except Exception as e:
            cls.get_logger().error(f"Error extracting task IDs: {str(e)}")
            return []

    @classmethod
    def extract_trip_id_from_info(cls, response_data: Dict[str, Any]) -> Optional[str]:
        return cls._extract_array_field(response_data, 'data', 'trip_id', 'trip ID from info')

    @classmethod
    def extract_trip_status(cls, response_data: Dict[str, Any]) -> Optional[str]:
        return cls._extract_array_field(response_data, 'data', 'status.display_name', 'trip status')

    @classmethod
    def extract_task_status(cls, response_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            status_code = cls._get_nested_value(response_data, 'data.0.status.status_code')
            display_name = cls._get_nested_value(response_data, 'data.0.status.display_name')
            
            status_info = {
                "status_code": str(status_code) if status_code else None,
                "display_name": str(display_name) if display_name else None
            }
            
            cls._log_extraction(status_info, 'task status', True)
            return status_info
        except Exception as e:
            cls.get_logger().error(f"Error extracting task status: {str(e)}")
            return {"status_code": None, "display_name": None}
