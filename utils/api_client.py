import time
from typing import Any, Dict, List, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.configmanager import ConfigManager
from utils.logger_utils import LoggerUtils
from utils.request_utils import RequestUtils
from utils.response_utils import ResponseUtils

DEFAULT_CONTENT_TYPE = "application/json"


class APIClient:
    _instance: Optional['APIClient'] = None
    _session: Optional[requests.Session] = None

    def __new__(cls) -> 'APIClient':
        if cls._instance is None:
            cls._instance = super(APIClient, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._session is None:
            self._setup_session()

    def _setup_session(self) -> None:
        self._session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PATCH", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        
        self._session.timeout = 30

    def clear_session(self) -> None:
        if self._session:
            self._session.cookies.clear()
            self.logger.debug("Session cookies cleared")

    @property
    def config_manager(self) -> ConfigManager:
        return ConfigManager()

    @property
    def logger(self):
        return LoggerUtils.get_logger(__name__)

    def get(self, endpoint: str, path_params: Dict[str, str] = None, 
            query_params: Dict[str, Any] = None, headers: Dict[str, str] = None,
            cookie: str = None) -> requests.Response:
        return self._make_request(
            method="GET",
            endpoint=endpoint,
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            cookie=cookie
        )

    def post(self, endpoint: str, data: Union[Dict[str, Any], List[Dict[str, Any]]] = None,
             path_params: Dict[str, str] = None, query_params: Dict[str, Any] = None,
             headers: Dict[str, str] = None, cookie: str = None,
             content_type: str = DEFAULT_CONTENT_TYPE) -> requests.Response:
        return self._make_request(
            method="POST",
            endpoint=endpoint,
            data=data,
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            cookie=cookie,
            content_type=content_type
        )

    def patch(self, endpoint: str, data: Union[Dict[str, Any], List[Dict[str, Any]]] = None,
              path_params: Dict[str, str] = None, query_params: Dict[str, Any] = None,
              headers: Dict[str, str] = None, cookie: str = None,
              content_type: str = DEFAULT_CONTENT_TYPE) -> requests.Response:
        return self._make_request(
            method="PATCH",
            endpoint=endpoint,
            data=data,
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            cookie=cookie,
            content_type=content_type
        )

    def put(self, endpoint: str, data: Union[Dict[str, Any], List[Dict[str, Any]]] = None,
            path_params: Dict[str, str] = None, query_params: Dict[str, Any] = None,
            headers: Dict[str, str] = None, cookie: str = None,
            content_type: str = DEFAULT_CONTENT_TYPE) -> requests.Response:
        return self._make_request(
            method="PUT",
            endpoint=endpoint,
            data=data,
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            cookie=cookie,
            content_type=content_type
        )

    def delete(self, endpoint: str, path_params: Dict[str, str] = None,
               query_params: Dict[str, Any] = None, headers: Dict[str, str] = None,
               cookie: str = None) -> requests.Response:
        return self._make_request(
            method="DELETE",
            endpoint=endpoint,
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            cookie=cookie
        )

    def _make_request(self, method: str, endpoint: str, 
                     data: Union[Dict[str, Any], List[Dict[str, Any]]] = None,
                     path_params: Dict[str, str] = None,
                     query_params: Dict[str, Any] = None,
                     headers: Dict[str, str] = None,
                     cookie: str = None,
                     content_type: str = DEFAULT_CONTENT_TYPE) -> requests.Response:
        start_time = time.time()
        
        try:
            base_url = self.config_manager.base_url
            url = RequestUtils.build_url(base_url, endpoint, path_params, query_params)
            
            request_headers = RequestUtils.build_headers(content_type, headers, cookie)
            
            request_data = None
            if data is not None:
                request_data = RequestUtils.prepare_request_data(data, content_type)
            
            LoggerUtils.log_api_request(method, url, request_headers, data)
            
            response = self._session.request(
                method=method,
                url=url,
                headers=request_headers,
                data=request_data if content_type != DEFAULT_CONTENT_TYPE else None,
                json=data if content_type == DEFAULT_CONTENT_TYPE else None
            )
            
            response_time = time.time() - start_time
            response_data = self._parse_response_data(response)
            LoggerUtils.log_api_response(response.status_code, response_data, response_time)
            
            return response
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            LoggerUtils.log_error(e, f"API request failed: {method} {endpoint}")
            LoggerUtils.log_api_response(0, {"error": str(e)}, response_time)
            raise
        except Exception as e:
            response_time = time.time() - start_time
            LoggerUtils.log_error(e, f"Unexpected error in API request: {method} {endpoint}")
            LoggerUtils.log_api_response(0, {"error": str(e)}, response_time)
            raise

    def _parse_response_data(self, response: requests.Response) -> Dict[str, Any]:
        try:
            if response.text:
                return ResponseUtils.parse_json_response(response.text)
        except ValueError:
            pass
        return {"raw_response": response.text}

    def make_request_with_response(self, method: str, endpoint: str, 
                                 data: Union[Dict[str, Any], List[Dict[str, Any]]] = None,
                                 path_params: Dict[str, str] = None,
                                 query_params: Dict[str, Any] = None,
                                 headers: Dict[str, str] = None,
                                 cookie: str = None,
                                 content_type: str = DEFAULT_CONTENT_TYPE) -> Dict[str, Any]:
        response = self._make_request(
            method=method,
            endpoint=endpoint,
            data=data,
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            cookie=cookie,
            content_type=content_type
        )
        
        response_data = self._parse_response_data(response)
        
        return {
            "response_data": response_data,
            "status_code": response.status_code,
            "success": ResponseUtils.validate_response_success(response_data)
        }
    
    def log_operation_result(self, operation: str, success: bool, **kwargs) -> None:
        status = "successful" if success else "failed"
        context = " ".join([f"{k}: {v}" for k, v in kwargs.items()])
        self.logger.info(f"{operation} {status}" + (f" - {context}" if context else ""))
