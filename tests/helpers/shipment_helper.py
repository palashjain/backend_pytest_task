import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from utils.shipment_client import ShipmentClient
from utils.logger_utils import LoggerUtils


class ShipmentHelper:
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 2
    MIN_SHIPMENTS_REQUIRED: int = 2
    REQUIRED_STATUS_FIELDS: List[str] = ["status_code", "display_name"]
    STATUS_CODES = {
        "CREATED": "CR",
        "DRIVER_ASSIGNED": "RA",
        "COMPLETED": "C",
        "DELIVERED": "DL"
    }
    DISPLAY_NAMES = {
        "PENDING": "Pending",
        "DRIVER_ASSIGNED": "Driver Assigned",
        "COMPLETED": "Completed",
        "DELIVERY_COMPLETED": "Delivery Completed"
    }
    
    def __init__(self, api_client: Any) -> None:
        self.api_client = api_client
        self.shipment_client = ShipmentClient(api_client)
        self.logger = LoggerUtils.get_logger(__name__)
    
    def create_multiple_shipments(self, shipment_data: Dict[str, Any], cookie: str) -> List[str]:
        self.logger.info("Creating multiple shipments for E2E test")
        
        result = self.shipment_client.create_shipment(shipment_data, cookie)
        
        if not self._is_shipment_creation_successful(result):
            error_msg = f"Failed to create shipments: {result}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        shipment_ids = self._extract_shipment_ids_from_response(result)
        self.logger.info(f"Successfully created {len(shipment_ids)} shipments: {shipment_ids}")
        return shipment_ids
    
    def fetch_all_shipments_with_retry(self, shipment_ids: List[str], cookie: str) -> Dict[str, Dict[str, Any]]:
        self.logger.info(f"Fetching all shipments with retry mechanism: {shipment_ids}")
        
        fetched_shipments, failed_shipments = self._fetch_multiple_shipments_with_retry(shipment_ids, cookie)
        
        self._log_fetch_results(fetched_shipments, failed_shipments, len(shipment_ids))
        return fetched_shipments
    
    def validate_shipment_status(self, shipment_id: str, expected_status_code: str, 
                                expected_display_name: str, cookie: str) -> bool:
        self.logger.info(f"Validating shipment {shipment_id} status: "
                        f"expected={expected_status_code}, display={expected_display_name}")
        
        shipment_data = self._fetch_shipment_with_retry(shipment_id, cookie)
        
        self._validate_shipment_id_match(shipment_data, shipment_id)
        self._validate_status_presence(shipment_data, shipment_id)
        self._validate_status_values(shipment_data, expected_status_code, 
                                   expected_display_name, shipment_id)
        
        self.logger.info(f"✅ Status validation passed for shipment {shipment_id}: "
                        f"{shipment_data.get('status_code')} - {shipment_data.get('display_name')}")
        return True

    def validate_shipments_status(self, shipment_ids: List[str], expected_status_code: str,
                                  expected_display_name: str, cookie: str) -> None:
        self.logger.info("=== Validating multiple shipments status ===")
        for shipment_id in shipment_ids:
            ok = self.validate_shipment_status(
                shipment_id=shipment_id,
                expected_status_code=expected_status_code,
                expected_display_name=expected_display_name,
                cookie=cookie
            )
            assert ok, f"Shipment {shipment_id} status validation failed"
    
    def create_and_validate_shipments(self, test_data_manager: Any, cookie: str) -> List[str]:
        self.logger.info("=== Starting E2E Test: Shipment Creation ===")
        
        shipment_data = test_data_manager.load_test_data("create_shipment_base_data.json")
        shipment_ids = self.create_multiple_shipments(shipment_data, cookie)
        
        self._validate_minimum_shipment_count(shipment_ids)
        
        fetched_shipments = self._fetch_and_validate_all_shipments(shipment_ids, cookie)
        
        self._validate_individual_shipments(shipment_ids, fetched_shipments)
        
        self.logger.info(f"✅ E2E Test completed successfully with {len(shipment_ids)} shipments")
        return shipment_ids
    
    def _validate_minimum_shipment_count(self, shipment_ids: List[str]) -> None:
        assert len(shipment_ids) >= self.MIN_SHIPMENTS_REQUIRED, \
            f"Expected at least {self.MIN_SHIPMENTS_REQUIRED} shipments, got {len(shipment_ids)}"
    
    def _fetch_and_validate_all_shipments(self, shipment_ids: List[str], cookie: str) -> Dict[str, Dict[str, Any]]:
        self.logger.info("=== Fetching all created shipments with retry mechanism ===")
        fetched_shipments = self.fetch_all_shipments_with_retry(shipment_ids, cookie)
        
        assert len(fetched_shipments) == len(shipment_ids), \
            f"Expected {len(shipment_ids)} fetched shipments, got {len(fetched_shipments)}"
        
        return fetched_shipments
    
    def _validate_individual_shipments(self, shipment_ids: List[str], 
                                     fetched_shipments: Dict[str, Dict[str, Any]]) -> None:
        for shipment_id in shipment_ids:
            assert shipment_id in fetched_shipments, \
                f"Shipment {shipment_id} not found in fetched shipments"
            
            shipment_data = fetched_shipments[shipment_id]
            self._validate_shipment_id_match(shipment_data, shipment_id)
            self._validate_status_presence(shipment_data, shipment_id)
            
            self.logger.info(f"✅ Validated shipment {shipment_id}: "
                           f"status_code={shipment_data['status_code']}, "
                           f"display_name={shipment_data['display_name']}")
    
    def _fetch_shipment_with_retry(self, awb_number: str, cookie: str) -> Dict[str, Any]:
        return self._fetch_with_retry(
            operation_name=f"fetch_shipment_{awb_number}",
            operation=lambda: self.shipment_client.fetch_shipment(awb_number, cookie),
            success_handler=lambda result: self._extract_shipment_data(result["response_data"]),
            failure_handler=lambda: {}
        )

    def _extract_shipment_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            data = response_data.get("data", {})
            
            shipment_id = self._extract_shipment_id(data)
            
            status_info = data.get("status", {})
            status_code = status_info.get("status_code")
            display_name = status_info.get("display_name")
            
            shipment_data = {
                "shipment_id": str(shipment_id) if shipment_id else "",
                "awb_number": str(shipment_id) if shipment_id else "",
                "status_code": status_code,
                "display_name": display_name,
                "full_status": status_info,
                "raw_data": data
            }
            
            self.logger.info(f"Extracted shipment data: ID={shipment_data['shipment_id']}, "
                           f"Status={status_code}, Display={display_name}")
            return shipment_data
            
        except Exception as e:
            self.logger.error(f"Error extracting shipment data: {str(e)}")
            return {}
    
    def _extract_shipment_id(self, data: Dict[str, Any]) -> Optional[str]:
        return (data.get("awb_number") or 
                data.get("id") or 
                data.get("shipment_id"))
    
    def _is_shipment_creation_successful(self, result: Dict[str, Any]) -> bool:
        return result.get("success", False) and bool(result.get("response_data", {}).get("data"))
    
    def _extract_shipment_ids_from_response(self, result: Dict[str, Any]) -> List[str]:
        try:
            awb_numbers = [entry["awb_number"] for entry in result["response_data"]["data"]]
            self.logger.info(f"Shipment creation successful with AWB numbers: {awb_numbers}")
            
            shipment_ids = [str(awb_number) for awb_number in awb_numbers]
            
            for shipment_id, awb_number in zip(shipment_ids, awb_numbers):
                self.logger.info(f"Created shipment with ID: {shipment_id} (AWB: {awb_number})")
            
            return shipment_ids
            
        except (KeyError, TypeError) as e:
            error_msg = f"Error extracting shipment IDs from response: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _fetch_multiple_shipments_with_retry(self, shipment_ids: List[str], cookie: str) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        fetched_shipments = {}
        failed_shipments = []
        
        for shipment_id in shipment_ids:
            fetched_shipment_data = self._fetch_shipment_with_retry(shipment_id, cookie)
            
            if self._is_valid_shipment_data(fetched_shipment_data):
                fetched_shipments[shipment_id] = fetched_shipment_data
                self.logger.info(f"✅ Successfully fetched shipment {shipment_id} "
                               f"with status {fetched_shipment_data.get('status_code')}")
            else:
                failed_shipments.append(shipment_id)
                self.logger.error(f"❌ Failed to fetch shipment {shipment_id}")
        
        return fetched_shipments, failed_shipments
    
    def _log_fetch_results(self, fetched_shipments: Dict[str, Dict[str, Any]], 
                          failed_shipments: List[str], total_count: int) -> None:
        if failed_shipments:
            self.logger.warning(f"Failed to fetch {len(failed_shipments)} shipments: {failed_shipments}")
        
        success_rate = (len(fetched_shipments) / total_count) * 100 if total_count > 0 else 0
        self.logger.info(f"Successfully fetched {len(fetched_shipments)}/{total_count} shipments "
                        f"({success_rate:.1f}% success rate)")
    
    def _fetch_with_retry(self, operation_name: str, operation: Callable, 
                         success_handler: Callable, failure_handler: Callable) -> Any:
        for attempt in range(self.MAX_RETRIES):
            self.logger.info(f"Attempt {attempt + 1}/{self.MAX_RETRIES} for {operation_name}")
            
            try:
                result = operation()
                
                if self._is_operation_successful(result):
                    self.logger.info(f"{operation_name} successful")
                    return success_handler(result)
                else:
                    self.logger.warning(f"Attempt {attempt + 1} failed: "
                                      f"status={result.get('status_code')}, "
                                      f"success={result.get('success')}")
                    
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed with exception: {str(e)}")
            
            if attempt < self.MAX_RETRIES - 1:
                self.logger.info(f"Retrying in {self.RETRY_DELAY_SECONDS} seconds...")
                time.sleep(self.RETRY_DELAY_SECONDS)
            else:
                self.logger.error(f"All attempts failed for {operation_name}")
        
        return failure_handler()
    
    def _is_operation_successful(self, result: Dict[str, Any]) -> bool:
        return result.get("status_code") == 200 and result.get("success", False)
    
    def _is_valid_shipment_data(self, shipment_data: Dict[str, Any]) -> bool:
        return bool(shipment_data and shipment_data.get("shipment_id"))
    
    def _validate_shipment_id_match(self, shipment_data: Dict[str, Any], expected_id: str) -> None:
        actual_id = shipment_data.get("shipment_id")
        assert actual_id == expected_id, \
            f"Fetched shipment ID {actual_id} doesn't match expected {expected_id}"
    
    def _validate_status_presence(self, shipment_data: Dict[str, Any], shipment_id: str) -> None:
        for field in self.REQUIRED_STATUS_FIELDS:
            assert shipment_data.get(field) is not None, \
                f"{field} not found for shipment {shipment_id}"
    
    def _validate_status_values(self, shipment_data: Dict[str, Any], 
                              expected_status_code: str, expected_display_name: str, 
                              shipment_id: str) -> None:
        actual_status_code = shipment_data.get("status_code")
        actual_display_name = shipment_data.get("display_name")
        
        assert actual_status_code == expected_status_code, \
            f"Expected status_code '{expected_status_code}', got '{actual_status_code}' for shipment {shipment_id}"
        
        assert actual_display_name == expected_display_name, \
            f"Expected display_name '{expected_display_name}', got '{actual_display_name}' for shipment {shipment_id}"