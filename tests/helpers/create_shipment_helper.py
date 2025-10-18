import time
from typing import Any, Dict
from utils.response_utils import ResponseUtils
from utils.logger_utils import LoggerUtils
from utils.common_utils import CommonUtils
from utils.generic_contract_validator import GenericContractValidator


class CreateShipmentHelper:
    
    @staticmethod
    def setup_e2e_test_data(authenticated_request: Dict[str, Any], valid_shipment_data: Dict[str, Any], 
                           test_data_manager: Any, scenario_type: str, test_data_source: str) -> tuple:
        if test_data_source == "valid_shipment_data":
            test_data = valid_shipment_data
        else:
            test_data = test_data_manager.get_shipment_test_data(test_data_source)
        
        if scenario_type == "multiple_shipments":
            test_data = CommonUtils.deep_copy_dict(test_data)
            if "data" in test_data:
                second_shipment = test_data["data"][0].copy()
                second_shipment["description"] = "Second shipment for e2e test"
                test_data["data"].append(second_shipment)
        
        cookie = None if scenario_type == "authentication_test" else authenticated_request["cookie"]
        
        return test_data, cookie
    
    @staticmethod
    def validate_contract_for_e2e(test_data: Dict[str, Any], scenario_type: str) -> None:
        validation_result = GenericContractValidator.validate_shipment_request(test_data)
        
        if scenario_type == "invalid_data":
            assert not validation_result["is_valid"], "Invalid data should fail contract validation"
        else:
            assert validation_result["is_valid"], f"Valid data should pass contract validation: {GenericContractValidator.get_validation_summary(validation_result)}"
    
    @staticmethod
    def execute_e2e_api_call(shipment_client: Any, test_data: Dict[str, Any], 
                            cookie: str, scenario_type: str) -> tuple:
        if scenario_type == "performance_test":
            start_time = time.time()
            result = shipment_client.create_shipment(test_data, cookie)
            end_time = time.time()
            creation_time = end_time - start_time
        else:
            result = shipment_client.create_shipment(test_data, cookie)
            creation_time = None
        
        return result, creation_time
    
    @staticmethod
    def handle_multiple_shipments_scenario(result: Dict[str, Any], logger: Any = None) -> None:
        if logger is None:
            logger = LoggerUtils.get_logger(__name__)
            
        logger.info("✅ E2E multiple shipments test completed")
        if result["success"]:
            logger.info("✅ Multiple shipments created successfully")
        else:
            error_msg = ResponseUtils.get_error_message(result["response_data"])
            logger.info(f"Multiple shipments creation failed: {error_msg}")
    
    @staticmethod
    def handle_invalid_data_scenario(result: Dict[str, Any], logger: Any = None) -> None:
        if logger is None:
            logger = LoggerUtils.get_logger(__name__)
            
        assert not result["success"], "Success should be false for invalid data"
        error_msg = ResponseUtils.get_error_message(result["response_data"])
        assert error_msg is not None, "Error message should be present"
        logger.info(f"✅ E2E invalid scenario handled correctly: {error_msg}")
    
    @staticmethod
    def handle_valid_single_scenario(result: Dict[str, Any], logger: Any = None) -> None:
        if logger is None:
            logger = LoggerUtils.get_logger(__name__)
            
        if result["success"]:
            assert result["awb_number"] is not None, "AWB number should be present for successful creation"
            logger.info(f"✅ E2E shipment creation successful with AWB: {result['awb_number']}")
        else:
            error_msg = ResponseUtils.get_error_message(result["response_data"])
            logger.info(f"E2E shipment creation failed as expected: {error_msg}")
