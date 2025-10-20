from typing import Dict, Any
from utils.api_client import APIClient
from utils.response_utils import ResponseUtils


class AuthClient:
    
    def __init__(self, api_client=None):
        self.api_client = api_client or APIClient()
    
    def login(self, username: str = None, password: str = None, user_type: str = "admin") -> Dict[str, Any]:
        if user_type.lower() == "rider":
            username = username or self.api_client.config_manager.rider_username
            password = password or self.api_client.config_manager.rider_password
            operation_name = "Rider login"
        else:
            username = username or self.api_client.config_manager.username
            password = password or self.api_client.config_manager.password
            operation_name = "Login"
        
        login_data = {
            "username": username,
            "password": password
        }
        
        endpoint = self.api_client.config_manager.get("API", "login_endpoint")
        result = self.api_client.make_request_with_response("POST", endpoint, data=login_data)
        
        workspace_id = ResponseUtils.extract_workspace_id(result["response_data"])
        cookie = ResponseUtils.extract_cookie_from_session(self.api_client._session.cookies)
        
        auth_data = {
            "cookie": cookie,
            "workspace_id": workspace_id,
            "response_data": result["response_data"],
            "status_code": result["status_code"]
        }
        
        self.api_client.log_operation_result(operation_name, True, username=username)
        return auth_data

    def workspace_login(self, workspace_id: str, cookie: str, user_type: str = "admin") -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "workspace_login_endpoint")
        endpoint = f"{endpoint}/{workspace_id}"
        
        result = self.api_client.make_request_with_response("PATCH", endpoint, cookie=cookie)
        
        workspace_cookie = ResponseUtils.extract_cookie_from_session(self.api_client._session.cookies)
        
        workspace_auth_data = {
            "response_data": result["response_data"],
            "status_code": result["status_code"],
            "cookie": workspace_cookie
        }
        
        operation_name = "Rider workspace login" if user_type.lower() == "rider" else "Workspace login"
        self.api_client.log_operation_result(operation_name, True, workspace_id=workspace_id)
        return workspace_auth_data

    def logout(self, cookie: str = None, user_type: str = "admin") -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "logout_endpoint")
        result = self.api_client.make_request_with_response("POST", endpoint, cookie=cookie)

        logout_data = {
            "response_data": result["response_data"],
            "status_code": result["status_code"]
        }

        operation_name = "Rider logout" if user_type.lower() == "rider" else "Logout"
        self.api_client.log_operation_result(operation_name, True)
        return logout_data

    def login_rider(self, username: str = None, password: str = None) -> Dict[str, Any]:
        return self.login(username, password, user_type="rider")
    
    def workspace_login_rider(self, workspace_id: str, cookie: str) -> Dict[str, Any]:
        return self.workspace_login(workspace_id, cookie, user_type="rider")
    
    def logout_rider(self, cookie: str = None) -> Dict[str, Any]:
        return self.logout(cookie, user_type="rider")
