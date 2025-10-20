from typing import Dict, Any, List
from utils.api_client import APIClient
from utils.response_utils import ResponseUtils


class TaskClient:
    
    def __init__(self, api_client=None):
        self.api_client = api_client or APIClient()

    def get_task_details(self, task_id: str, cookie: str) -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "task_details_endpoint")
        
        query_params = {"task_id": task_id}
        result = self.api_client.make_request_with_response(
            "GET", endpoint, query_params=query_params, cookie=cookie
        )
        
        status_code = None
        display_name = None
        
        if result["success"]:
            status_info = ResponseUtils.extract_task_status(result["response_data"])
            status_code = status_info.get("status_code")
            display_name = status_info.get("display_name")
        
        result["task_status_code"] = status_code
        result["task_display_name"] = display_name
        
        self.api_client.log_operation_result("Task details fetch", result["success"], task_id=task_id)
        
        return result

    def update_task_status(self, task_status_data: Dict[str, Any], cookie: str) -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "task_status_endpoint")
        
        result = self.api_client.make_request_with_response("PUT", endpoint, data=task_status_data, cookie=cookie)
        
        self.api_client.log_operation_result("Task status update", result["success"])
        
        return result

    def submit_task_otp(self, task_id: str, otp_data: Dict[str, Any], cookie: str) -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "task_otp_endpoint")
        endpoint = f"{endpoint}/{task_id}/proof_of_work/otp"
        
        result = self.api_client.make_request_with_response("POST", endpoint, data=otp_data, cookie=cookie)
        
        self.api_client.log_operation_result("Task OTP submission", result["success"], task_id=task_id)
        
        return result
