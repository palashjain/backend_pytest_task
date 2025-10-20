import pytest
import allure
import time
from utils.api_client import APIClient
from utils.shipment_client import ShipmentClient
from utils.logger_utils import LoggerUtils
from utils.file_utils import FileUtils
from tests.helpers import CommonHelper


@pytest.mark.shipment
class TestCreateShipment:

    def setup_method(self):
        self.shipment_client = ShipmentClient(self.api_client)
        self.logger = LoggerUtils.get_logger(__name__)

    @pytest.mark.skip(reason="Skipping this test as it is already covered in the E2E test: test_shipment_e2e_complete_flow")
    @allure.title("Test Shipment Creation - Valid Data")
    @allure.description("Test shipment creation with valid data structure and validate by fetching the created shipment")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_shipment_creation_valid_data(self, authenticated_request, test_data_manager):
        cookie = authenticated_request["cookie"]
        
        shipment_data = test_data_manager.load_test_data("create_shipment_base_data.json")
        
        create_shipment_response = self.shipment_client.create_shipment(shipment_data, cookie)
        
        assert create_shipment_response["status_code"] == 200, f"Expected status code 200, got {create_shipment_response['status_code']}"
        assert create_shipment_response["success"], "Shipment creation should be successful"
        awb_number = create_shipment_response["awb_number"]
        assert awb_number is not None, "AWB number should be present for successful creation"
        self.logger.info(f"Shipment created successfully with AWB: {awb_number}")
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            self.logger.info(f"Fetch attempt {attempt + 1}/{max_retries} for AWB: {awb_number}")
            fetch_shipment_result = self.shipment_client.fetch_shipment(awb_number, cookie)
            
            if fetch_shipment_result["status_code"] == 200 and fetch_shipment_result["success"]:
                self.logger.info(f"Shipment fetch successful for AWB: {awb_number}")
                break
            else:
                self.logger.warning(f"Fetch attempt {attempt + 1} failed: status={fetch_shipment_result['status_code']}, success={fetch_shipment_result['success']}")
                if attempt < max_retries:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"All fetch attempts failed for AWB: {awb_number}")
        
        assert fetch_shipment_result["status_code"] == 200 and fetch_shipment_result["success"], "Shipment fetch should be successful"
        fetch_data = fetch_shipment_result["response_data"]
        assert fetch_data is not None, "Fetch response data should not be None"
        self.logger.info("Shipment creation and fetch validation completed successfully")

    @pytest.mark.regression
    @allure.title("Test Shipment Creation - Comprehensive Validation")
    @allure.description("Test shipment creation with comprehensive validation scenarios including missing fields, enum, data type, format, boundary, string length, basic, location, item, and invoice validations")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("validation_type,field_path,invalid_value,expected_error,description,test_category", 
                            FileUtils.get_parametrize_data_from_csv(
                                "validation_test_data.csv",
                                ["validation_type", "field_path", "missing_field/invalid_value", "expected_error", "description", "test_category"]
                            ))
    def test_shipment_creation_comprehensive_validation(self, authenticated_request, valid_shipment_data, validation_type, field_path, invalid_value, expected_error, description, test_category):
        cookie = authenticated_request["cookie"]
        
        if validation_type == "missing_field_validation":
            test_data = CommonHelper.create_test_data_with_missing_field(valid_shipment_data, field_path)
            self.logger.info(f"Testing missing field: {field_path}")
        else:
            test_data = CommonHelper.modify_test_data_for_validation(valid_shipment_data, validation_type, field_path, invalid_value)
            self.logger.info(f"Testing {validation_type} on {field_path} with value: {invalid_value}")
        
        result = self.shipment_client.create_shipment(test_data, cookie)
        
        if validation_type == "missing_field_validation":
            assert result["status_code"] == 200, f"Expected status code 200, got {result['status_code']}"
            self.logger.info(f"Required field validation test passed for {field_path}")
        else:
            CommonHelper.validate_field_validation_response(result, validation_type, field_path, invalid_value, expected_error, self.logger)
            self.logger.info(f"✅ {test_category.upper()} validation test completed: {description}")

    @pytest.mark.regression
    @allure.title("Test Shipment Creation - Parametrized Null Values")
    @allure.description("Test shipment creation with null values in various required fields")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("field_path,expected_error", [
        ("description", "shipment_validation_failed"),
        ("courier_identifier", "shipment_validation_failed"),
        ("pickup_location.name", "schema_validation_failed"),
        ("drop_location.name", "schema_validation_failed"),
        ("items.0.name", "shipment_validation_failed"),
    ])
    def test_shipment_creation_null_values_parametrized(self, authenticated_request, valid_shipment_data, field_path, expected_error):
        cookie = authenticated_request["cookie"]
        
        invalid_data = CommonHelper.modify_test_data_for_validation(valid_shipment_data, "basic", field_path, None)
        
        self.logger.info(f"Testing null values on field: {field_path}")
        
        result = self.shipment_client.create_shipment(invalid_data, cookie)
        
        CommonHelper.validate_field_validation_response(result, "null_validation", field_path, None, expected_error, self.logger)
 