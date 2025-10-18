from typing import Any, Dict, List, Optional, Union
from utils.file_utils import FileUtils
from utils.logger_utils import LoggerUtils
from utils.common_utils import CommonUtils
from config.api_config_manager import APIConfigManager
from faker import Faker


class GenericDataManager:
    _instance: Optional['GenericDataManager'] = None
    _faker: Optional[Any] = None

    def __new__(cls) -> 'GenericDataManager':
        if cls._instance is None:
            cls._instance = super(GenericDataManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, '_logger'):
            self._logger = LoggerUtils.get_logger(__name__)
            self._api_config_manager = APIConfigManager()
            
        if self._faker is None:
            try:
                self._faker = Faker()
            except ImportError:
                self._faker = None
                self._logger.warning("Faker not available - random data generation will be limited")

    def load_test_data(self, file_name: str, file_type: str = "json") -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        return CommonUtils.log_and_raise(FileUtils.load_test_data, file_name, file_type)

    def get_api_test_data(self, api_name: str) -> Dict[str, Any]:
        def _get_data():
            base_data_file = self._api_config_manager.get_base_data_file(api_name)
            base_data = self.load_test_data(base_data_file)
            
            # Enhance base data with missing required fields
            if api_name == "create_shipment":
                base_data = self._enhance_shipment_base_data(base_data)
            
            return base_data
        
        return CommonUtils.log_and_raise(_get_data)

    def _enhance_shipment_base_data(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        enhanced_data = CommonUtils.deep_copy_dict(base_data)
        
        if not self._has_valid_shipment_data(enhanced_data):
            return enhanced_data
            
        shipment = enhanced_data["data"][0]
        
        self._enhance_items(shipment)
        self._enhance_location(shipment, "pickup_location", self._get_pickup_location_defaults())
        self._enhance_location(shipment, "drop_location", self._get_drop_location_defaults())
        self._enhance_invoice(shipment)
        self._enhance_shipment_fields(shipment)
        
        return enhanced_data

    def _has_valid_shipment_data(self, data: Dict[str, Any]) -> bool:
        return (
            isinstance(data, dict) and 
            "data" in data and 
            isinstance(data["data"], list) and 
            len(data["data"]) > 0 and
            isinstance(data["data"][0], dict)
        )

    def _enhance_items(self, shipment: Dict[str, Any]) -> None:
        if "items" not in shipment or not shipment["items"]:
            return
            
        item_defaults = {
            "id": 1,
            "currency_code": "INR",
            "gst": {"cgst": 9, "sgst": 9, "igst": 18}
        }
        
        for item in shipment["items"]:
            self._apply_defaults(item, item_defaults)

    def _enhance_location(self, shipment: Dict[str, Any], location_key: str, defaults: Dict[str, Any]) -> None:
        if location_key not in shipment:
            return
            
        location = shipment[location_key]
        self._apply_defaults(location, defaults)
        
        if "contact_details" in location and isinstance(location["contact_details"], dict):
            self._apply_defaults(location["contact_details"], {"isd_code": "91"})
        
        if "pincode" in location and isinstance(location["pincode"], int):
            location["pincode"] = str(location["pincode"])
        
        if "location_name" not in location and "name" in location:
            location["location_name"] = location["name"]

    def _enhance_invoice(self, shipment: Dict[str, Any]) -> None:
        if "invoice" not in shipment:
            return
            
        invoice = shipment["invoice"]
        invoice_defaults = {
            "currency_code": "INR",
            "seller_gstin": "22ABCDE1234F1Z5",
            "gst": {"cgst": 9, "sgst": 9, "igst": 18}
        }
        
        self._apply_defaults(invoice, invoice_defaults)
        
        if "invoice_number" in invoice and isinstance(invoice["invoice_number"], int):
            invoice["invoice_number"] = str(invoice["invoice_number"])
        elif "invoice_number" not in invoice:
            invoice["invoice_number"] = "12345"

    def _enhance_shipment_fields(self, shipment: Dict[str, Any]) -> None:
        if "e_waybill" in shipment and shipment["e_waybill"] is None:
            shipment["e_waybill"] = "EWB123456789012345"

    def _apply_defaults(self, target: Dict[str, Any], defaults: Dict[str, Any]) -> None:
        for key, default_value in defaults.items():
            if key not in target or not target[key]:
                target[key] = default_value

    def _get_pickup_location_defaults(self) -> Dict[str, Any]:
        return {
            "id": 1,
            "description": "Pickup location description",
            "complete_after": "2023-04-03T09:00:00Z",
            "complete_before": "2023-04-03T18:00:00Z",
            "otp_required": False,
            "image_required": False,
            "signature_required": False,
            "notes_required": False,
            "form_required": False,
            "location_hash": "hash123",
            "location_name": "Pickup Location",
            "slot_id": 123,
            "serviceability_code": "SERV001"
        }

    def _get_drop_location_defaults(self) -> Dict[str, Any]:
        return {
            "id": 2,
            "description": "Drop location description",
            "complete_after": "2023-04-03T09:00:00Z",
            "complete_before": "2023-04-03T18:00:00Z",
            "otp_required": False,
            "image_required": False,
            "signature_required": False,
            "notes_required": False,
            "form_required": False,
            "location_hash": "hash456",
            "location_name": "Drop Location",
            "slot_id": 456,
            "serviceability_code": "SERV001"
        }

    def get_shipment_test_data(self) -> Dict[str, Any]:
        return self.get_api_test_data("create_shipment")
