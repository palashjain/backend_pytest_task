import json
from typing import Any, Dict, List, Union
from urllib.parse import urlencode, urljoin
from utils.base_utils import BaseClassUtils

DEFAULT_CONTENT_TYPE = "application/json"


class RequestUtils(BaseClassUtils):

    @classmethod
    def build_url(cls, base_url: str, endpoint: str, path_params: Dict[str, str] = None, 
                  query_params: Dict[str, Any] = None) -> str:
        try:
            url = urljoin(base_url.rstrip('/') + '/', endpoint.lstrip('/'))
            
            if path_params:
                for key, value in path_params.items():
                    url = url.replace(f'{{{key}}}', str(value))
                    url = url.replace(f':{key}', str(value))
            
            if query_params:
                filtered_params = {k: v for k, v in query_params.items() if v is not None}
                if filtered_params:
                    query_string = urlencode(filtered_params, doseq=True)
                    url = f"{url}?{query_string}"
            
            cls.get_logger().debug(f"Built URL: {url}")
            return url
        except Exception as e:
            cls.get_logger().error(f"Error building URL: {str(e)}")
            raise

    @classmethod
    def build_headers(cls, content_type: str = DEFAULT_CONTENT_TYPE, 
                     additional_headers: Dict[str, str] = None,
                     cookie: str = None) -> Dict[str, str]:
        try:
            headers = {
                'Content-Type': content_type,
                'Accept': 'application/json',
                'User-Agent': 'API-Test-Framework/1.0'
            }
            
            if cookie:
                headers['Cookie'] = cookie
            
            if additional_headers:
                headers.update(additional_headers)
            
            cls.get_logger().debug(f"Built headers: {headers}")
            return headers
        except Exception as e:
            cls.get_logger().error(f"Error building headers: {str(e)}")
            raise

    @classmethod
    def prepare_request_data(cls, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                           content_type: str = DEFAULT_CONTENT_TYPE) -> Union[str, Dict[str, Any]]:
        try:
            if content_type == DEFAULT_CONTENT_TYPE:
                if isinstance(data, (dict, list)):
                    return json.dumps(data, default=str)
                else:
                    return str(data)
            elif content_type == "application/x-www-form-urlencoded":
                if isinstance(data, dict):
                    return data
                else:
                    raise ValueError("Form data must be a dictionary")
            else:
                return data
        except Exception as e:
            cls.get_logger().error(f"Error preparing request data: {str(e)}")
            raise




