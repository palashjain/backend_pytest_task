from typing import Dict, Any, List
from utils.api_client import APIClient
from utils.response_utils import ResponseUtils


class TripClient:
    
    def __init__(self, api_client=None):
        self.api_client = api_client or APIClient()

    def create_trip(self, trip_data: Dict[str, Any], cookie: str) -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "create_trip_endpoint")
        
        result = self.api_client.make_request_with_response("POST", endpoint, data=trip_data, cookie=cookie)
        
        trip_id = None
        if result["success"]:
            trip_id = ResponseUtils.extract_trip_id(result["response_data"])
        
        result["trip_id"] = trip_id
        self.api_client.log_operation_result("Trip creation", result["success"])
        
        return result

    def get_trip_info(self, shipment_id: str, cookie: str) -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "trip_info_endpoint")
        endpoint = f"{endpoint}/{shipment_id}/trip-info"
        
        result = self.api_client.make_request_with_response("GET", endpoint, cookie=cookie)
        
        task_ids = []
        trip_id = None
        status = None
        
        if result["success"]:
            task_ids = ResponseUtils.extract_task_ids(result["response_data"])
            trip_id = ResponseUtils.extract_trip_id_from_info(result["response_data"])
            status = ResponseUtils.extract_trip_status(result["response_data"])
        
        result["task_ids"] = task_ids
        result["trip_id"] = trip_id
        result["status"] = status
        
        self.api_client.log_operation_result("Trip info fetch", result["success"], shipment_id=shipment_id)
        
        return result

    def update_trip_status(self, trip_status_data: Dict[str, Any], cookie: str) -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "trip_status_endpoint")
        
        result = self.api_client.make_request_with_response("PUT", endpoint, data=trip_status_data, cookie=cookie)
        
        self.api_client.log_operation_result("Trip status update", result["success"])
        
        return result

    def fetch_trip_status(self, trip_id: str, cookie: str) -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "trip_status_fetch_endpoint")
        endpoint = f"{endpoint}/{trip_id}"
        
        result = self.api_client.make_request_with_response("GET", endpoint, cookie=cookie)
        
        self.api_client.log_operation_result("Trip status fetch", result["success"], trip_id=trip_id)
        
        return result
