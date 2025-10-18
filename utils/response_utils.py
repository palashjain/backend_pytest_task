import json
from typing import Any, Dict, List, Optional, Union
from utils.base_utils import BaseClassUtils
from utils.common_utils import CommonUtils


class ResponseUtils(BaseClassUtils):

    @classmethod
    def parse_json_response(cls, response_text: str) -> Dict[str, Any]:
        def _parse():
            return json.loads(response_text)
        
        try:
            return _parse()
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
        try:
            value = cls._get_nested_value(response_data, 'user.workspace[0].urmId')
            if value:
                cls.get_logger().debug(f"Extracted workspace ID: {value}")
                return str(value)
            
            cls.get_logger().warning("Workspace ID not found in response")
            return None
        except Exception as e:
            cls.get_logger().error(f"Error extracting workspace ID: {str(e)}")
            return None


    @classmethod
    def extract_awb_number(cls, response_data: Dict[str, Any]) -> Optional[str]:
        try:
            value = cls._get_nested_value(response_data, 'data[0].awb_number')
            if value:
                cls.get_logger().debug(f"Extracted AWB number: {value}")
                return str(value)
            
            cls.get_logger().warning("AWB number not found in response")
            return None
        except Exception as e:
            cls.get_logger().error(f"Error extracting AWB number: {str(e)}")
            return None

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
        try:
            error_msg = cls._get_nested_value(response_data, 'failed_entries.0.message')
            if error_msg:
                return str(error_msg)
            
            return None
        except Exception as e:
            cls.get_logger().error(f"Error extracting error message: {str(e)}")
            return None
