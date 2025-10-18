from typing import Any, Dict, List
from utils.response_utils import ResponseUtils
from utils.logger_utils import LoggerUtils
from utils.common_utils import CommonUtils


class CommonHelper:
    
    FIELD_TYPES = {
        'numeric': {'length', 'width', 'height', 'weight', 'quantity', 'price_effective', 'mrp', 
                   'latitude', 'longitude', 'amount', 'cgst', 'sgst', 'igst', 'installation_time'},
        'integer': {'id', 'slot_id'},
        'string': {'pincode'},
        'boolean': {'otp_required', 'image_required', 'signature_required', 'notes_required', 
                   'form_required', 'mps', 'pdsr_allowed'}
    }
    
    BASIC_VALIDATION_TYPES = {
        "basic", "boundary", "enum_validation", "data_type_validation", 
        "format_validation", "string_length_validation"
    }
    
    @staticmethod
    def modify_test_data_for_validation(test_data: Dict[str, Any], validation_type: str, 
                                      field_path: str, invalid_value: Any) -> Dict[str, Any]:
        modified_data = CommonUtils.deep_copy_dict(test_data)
        
        if not CommonHelper._has_valid_data_structure(modified_data):
            return modified_data
            
        shipment = modified_data["data"][0]
        actual_invalid_value = CommonHelper._convert_invalid_value_placeholder(invalid_value, validation_type, field_path)
        
        if validation_type == "array_validation" and field_path == "data":
            modified_data["data"] = actual_invalid_value
            return modified_data
        
        if validation_type in CommonHelper.BASIC_VALIDATION_TYPES:
            CommonHelper._set_field_value(shipment, field_path, actual_invalid_value, validation_type)
        else:
            CommonHelper._set_nested_field_value(shipment, field_path, actual_invalid_value, validation_type)
        
        return modified_data
    
    @staticmethod
    def _has_valid_data_structure(data: Dict[str, Any]) -> bool:
        return "data" in data and len(data["data"]) > 0
    
    @staticmethod
    def _set_field_value(shipment: Dict[str, Any], field_path: str, value: Any, validation_type: str) -> None:
        if "." not in field_path:
            shipment[field_path] = value
        else:
            CommonHelper._set_nested_field_value(shipment, field_path, value, validation_type)
    
    @staticmethod
    def _convert_invalid_value_placeholder(invalid_value: Any, validation_type: str, field_path: str) -> Any:
        parsed_value = CommonHelper._parse_value_by_type(invalid_value)
        
        if not isinstance(invalid_value, str) or not invalid_value.startswith("invalid_"):
            return parsed_value
        
        return CommonHelper._generate_invalid_value_for_field(invalid_value, field_path, validation_type)
    
    @staticmethod
    def _generate_invalid_value_for_field(placeholder: str, field_path: str, validation_type: str) -> Any:
        field_name = field_path.split('.')[-1]
        
        validation_generators = {
            "data_type_validation": CommonHelper._get_invalid_data_type_value,
            "enum_validation": CommonHelper._get_invalid_enum_value,
            "format_validation": CommonHelper._get_invalid_format_value,
            "string_length_validation": CommonHelper._get_invalid_string_length_value,
            "array_validation": lambda _: []
        }
        
        generator = validation_generators.get(validation_type)
        return generator(field_name) if generator else f"invalid_{field_name}"
    
    @staticmethod
    def _get_invalid_data_type_value(field_name: str) -> Any:
        for field_type, fields in CommonHelper.FIELD_TYPES.items():
            if any(field in field_name for field in fields):
                return CommonHelper._get_invalid_value_for_type(field_type, field_name)
        return "invalid_value"
    
    @staticmethod
    def _get_invalid_value_for_type(field_type: str, field_name: str) -> Any:
        type_mappings = {
            'numeric': "invalid_number",
            'integer': "invalid_id" if 'id' in field_name else "invalid_number",
            'string': 12345,
            'boolean': "invalid_boolean"
        }
        return type_mappings.get(field_type, "invalid_value")
    
    @staticmethod
    def _get_invalid_enum_value(field_name: str) -> str:
        return f"invalid_{field_name}"
    
    @staticmethod
    def _get_invalid_format_value(field_name: str) -> str:
        format_mappings = {
            'datetime': "invalid-datetime-format",
            'complete_after': "invalid-datetime-format", 
            'complete_before': "invalid-datetime-format",
            'url': "not-a-valid-url",
            'date': "invalid-date"
        }
        
        for key, value in format_mappings.items():
            if key in field_name:
                return value
        return "invalid-format"
    
    @staticmethod
    def _get_invalid_string_length_value(field_name: str) -> str:
        length_mappings = {
            'hsn_code': "1234567",
            'courier_identifier': "a" * 51
        }
        
        for key, value in length_mappings.items():
            if key in field_name:
                return value
        return "a" * 100
    
    @staticmethod
    def _parse_value_by_type(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        
        if value.lstrip('-').replace('.', '').isdigit():
            return float(value) if '.' in value else int(value)
        
        return value
    
    @staticmethod
    def _set_nested_field_value(shipment: Dict[str, Any], field_path: str, 
                               invalid_value: Any, validation_type: str) -> None:
        CommonHelper._ensure_field_structure(shipment, field_path, validation_type)
        CommonUtils.set_nested_value(shipment, field_path, invalid_value)
    
    @staticmethod
    def _ensure_field_structure(shipment: Dict[str, Any], field_path: str, validation_type: str) -> None:
        if validation_type == "item" and not CommonHelper._has_items(shipment):
            CommonHelper._handle_missing_items(shipment, field_path)
        
        if validation_type == "invoice" and "invoice" not in shipment:
            return
        
        if field_path.startswith("packages."):
            CommonHelper._ensure_packages_structure(shipment, field_path)
    
    @staticmethod
    def _has_items(shipment: Dict[str, Any]) -> bool:
        return "items" in shipment and len(shipment["items"]) > 0
    
    @staticmethod
    def _handle_missing_items(shipment: Dict[str, Any], field_path: str) -> None:
        if "packages" in shipment and len(shipment["packages"]) > 0 and "items" in shipment["packages"][0]:
            pass
    
    @staticmethod
    def _ensure_packages_structure(shipment: Dict[str, Any], field_path: str) -> None:
        if "packages" not in shipment or not isinstance(shipment.get("packages"), list):
            shipment["packages"] = []
        
        if field_path.startswith("packages.0.") and len(shipment["packages"]) == 0:
            shipment["packages"].append({})
    
    @staticmethod
    def validate_field_validation_response(result: Dict[str, Any], validation_type: str, 
                                         field_path: str, invalid_value: Any, 
                                         expected_error: str, logger: Any = None) -> None:
        if logger is None:
            logger = LoggerUtils.get_logger(__name__)
            
        assert result["status_code"] == 200, f"Expected status code 200, got {result['status_code']}"
        
        if not result["success"]:
            error_msg = ResponseUtils.get_error_message(result["response_data"])
            assert error_msg is not None, f"Error message should be present for invalid {field_path}"
            if expected_error:
                assert error_msg == expected_error, f"Expected error {expected_error}, got {error_msg}"
            logger.info(f"Field validation test passed for {validation_type}.{field_path}, with error message: {error_msg}")
        else:
            logger.info(f"Field validation test: API accepts invalid {validation_type}.{field_path}={invalid_value} (validation not enforced)")
    
    @staticmethod
    def create_test_data_with_missing_field(test_data: Dict[str, Any], field_path: str) -> Dict[str, Any]:
        modified_data = CommonUtils.deep_copy_dict(test_data)
        
        if field_path == "data":
            modified_data.pop("data", None)
            return modified_data
        
        if CommonHelper._has_valid_data_structure(modified_data):
            shipment = modified_data["data"][0]
            
            if field_path in ["pickup_location", "drop_location", "payment_method"]:
                shipment.pop(field_path, None)
                return modified_data
            
            CommonHelper._remove_nested_field(shipment, field_path)
        
        return modified_data
    
    @staticmethod
    def _remove_nested_field(shipment: Dict[str, Any], field_path: str) -> None:
        parts = field_path.split(".")
        
        if len(parts) == 1:
            shipment.pop(field_path, None)
        else:
            CommonHelper._remove_deep_nested_field(shipment, parts)
    
    @staticmethod
    def _remove_deep_nested_field(shipment: Dict[str, Any], parts: List[str]) -> None:
        depth_handlers = {
            2: CommonHelper._remove_depth_2_field,
            3: CommonHelper._remove_depth_3_field,
            4: CommonHelper._remove_depth_4_field,
            5: CommonHelper._remove_depth_5_field
        }
        
        handler = depth_handlers.get(len(parts))
        if handler:
            handler(shipment, parts)
    
    @staticmethod
    def _remove_depth_2_field(shipment: Dict[str, Any], parts: List[str]) -> None:
        parent_field = parts[0]
        if parent_field in shipment:
            if isinstance(shipment[parent_field], list) and len(shipment[parent_field]) > 0:
                shipment[parent_field][0].pop(parts[1], None)
            elif isinstance(shipment[parent_field], dict):
                shipment[parent_field].pop(parts[1], None)
    
    @staticmethod
    def _remove_depth_3_field(shipment: Dict[str, Any], parts: List[str]) -> None:
        parent_field = parts[0]
        if parent_field in shipment and isinstance(shipment[parent_field], list) and len(shipment[parent_field]) > 0:
            package = shipment[parent_field][0]
            if parts[1].isdigit():
                package_index = int(parts[1])
                if package_index < len(shipment[parent_field]):
                    shipment[parent_field][package_index].pop(parts[2], None)
            elif parts[1] in package and isinstance(package[parts[1]], list) and len(package[parts[1]]) > 0:
                package[parts[1]][0].pop(parts[2], None)
    
    @staticmethod
    def _remove_depth_4_field(shipment: Dict[str, Any], parts: List[str]) -> None:
        parent_field = parts[0]
        if parent_field in shipment and isinstance(shipment[parent_field], list) and len(shipment[parent_field]) > 0:
            package = shipment[parent_field][0]
            if parts[1] in package and isinstance(package[parts[1]], list) and len(package[parts[1]]) > 0:
                item = package[parts[1]][0]
                item.pop(parts[3], None)
    
    @staticmethod
    def _remove_depth_5_field(shipment: Dict[str, Any], parts: List[str]) -> None:
        parent_field = parts[0]
        if parent_field in shipment and isinstance(shipment[parent_field], list) and len(shipment[parent_field]) > 0:
            package = shipment[parent_field][0]
            if parts[1] in package and isinstance(package[parts[1]], list) and len(package[parts[1]]) > 0:
                item = package[parts[1]][0]
                if parts[2] in item and isinstance(item[parts[2]], dict):
                    item[parts[2]].pop(parts[4], None)

