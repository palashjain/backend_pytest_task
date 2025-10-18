from typing import Dict, Any, List, Union
from utils.api_client import APIClient
from utils.response_utils import ResponseUtils


class ShipmentClient:
    
    def __init__(self, api_client=None):
        self.api_client = api_client or APIClient()

    def create_shipment(self, shipment_data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                       cookie: str) -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "create_shipment_endpoint")
        
        result = self.api_client.make_request_with_response("POST", endpoint, data=shipment_data, cookie=cookie)
        
        awb_number = None
        if result["success"]:
            awb_number = ResponseUtils.extract_awb_number(result["response_data"])
        
        result["awb_number"] = awb_number
        self.api_client.log_operation_result("Shipment creation", result["success"])
        
        return result

    def fetch_shipment(self, awb_number: str, cookie: str) -> Dict[str, Any]:
        endpoint = self.api_client.config_manager.get("API", "fetch_shipment_endpoint")
        endpoint = f"{endpoint}/{awb_number}"
        
        result = self.api_client.make_request_with_response("GET", endpoint, cookie=cookie)
        self.api_client.log_operation_result("Shipment fetch", result["success"], awb_number=awb_number)
        
        return result
