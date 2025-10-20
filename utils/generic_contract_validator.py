from typing import Any, Dict
from jsonschema import Draft7Validator, FormatChecker
from datetime import datetime
from utils.base_utils import BaseClassUtils
from schemas.schema_loader import SchemaLoader
from config.api_config_manager import APIConfigManager


class GenericContractValidator(BaseClassUtils):
    _api_config_manager = APIConfigManager()
    
    @classmethod
    def _create_format_checker(cls) -> FormatChecker:
        checker = FormatChecker()
        
        def check_datetime(instance):
            if not isinstance(instance, str):
                return True
            try:
                datetime.fromisoformat(instance.replace('Z', '+00:00'))
                return True
            except ValueError:
                return False
        
        checker.checks("date-time")(check_datetime)
        return checker

    @classmethod
    def get_schema(cls, api_name: str) -> Dict[str, Any]:
        schema_file = cls._api_config_manager.get_schema_file(api_name)
        schema_name = schema_file.replace('.json', '')
        return SchemaLoader.load_schema(schema_name)

    @classmethod
    def validate_request(cls, api_name: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            schema = cls.get_schema(api_name)
            validator = Draft7Validator(schema, format_checker=cls._create_format_checker())
            errors = list(validator.iter_errors(request_data))
            
            validation_result = {
                "is_valid": len(errors) == 0,
                "errors": []
            }
            
            for error in errors:
                error_info = {
                    "message": error.message,
                    "path": list(error.absolute_path),
                    "schema_path": list(error.absolute_schema_path),
                    "validator": error.validator,
                    "validator_value": error.validator_value
                }
                validation_result["errors"].append(error_info)
                cls.get_logger().warning(f"Validation error: {error.message} at path: {list(error.absolute_path)}")
            
            if validation_result["is_valid"]:
                cls.get_logger().info(f"{api_name} request validation passed")
            else:
                cls.get_logger().warning(f"{api_name} request validation failed with {len(errors)} errors")
            
            return validation_result
            
        except Exception as e:
            cls.get_logger().error(f"Error during {api_name} contract validation: {str(e)}")
            return {
                "is_valid": False,
                "errors": [{"message": f"Validation error: {str(e)}", "path": [], "schema_path": [], "validator": "exception", "validator_value": None}]
            }


    @classmethod
    def get_validation_summary(cls, validation_result: Dict[str, Any]) -> str:
        if validation_result["is_valid"]:
            return "Validation passed successfully"
        
        error_count = len(validation_result["errors"])
        summary = f"Validation failed with {error_count} error(s):\n"
        
        for i, error in enumerate(validation_result["errors"][:5], 1):
            path_str = " -> ".join(str(p) for p in error["path"]) if error["path"] else "root"
            summary += f"{i}. {error['message']} (at: {path_str})\n"
        
        if error_count > 5:
            summary += f"... and {error_count - 5} more errors"
        
        return summary


    @classmethod
    def validate_shipment_request(cls, request_data: Dict[str, Any]) -> Dict[str, Any]:
        return cls.validate_request("create_shipment", request_data)

    @classmethod
    def get_shipment_schema(cls) -> Dict[str, Any]:
        return cls.get_schema("create_shipment")
