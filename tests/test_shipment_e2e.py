import pytest
import allure
import time
from utils.api_client import APIClient
from utils.logger_utils import LoggerUtils
from tests.helpers.shipment_helper import ShipmentHelper
from tests.helpers.trip_helper import TripHelper
from tests.helpers.task_helper import TaskHelper
from tests.helpers.auth_helper import AuthHelper


@pytest.mark.shipment
class TestShipmentE2EFlow:

    def setup_method(self):
        self.shipment_helper = ShipmentHelper(self.api_client)
        self.trip_helper = TripHelper(self.api_client)
        self.task_helper = TaskHelper(self.api_client)
        self.auth_helper = AuthHelper(self.api_client)
        self.logger = LoggerUtils.get_logger(__name__)
        self.rider_cookie = None
        self.regular_cookie = None

    @pytest.mark.e2e
    @allure.title("End-to-End Shipment Flow: Creation, Trip Assignment, Task Execution")
    @allure.description("Complete end-to-end test covering shipment creation, trip creation, task assignment, and task completion by rider")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_shipment_e2e_complete_flow(self, authenticated_request, test_data_manager):
        cookie = authenticated_request["cookie"]
        self.regular_cookie = cookie
        
        shipment_ids = self.shipment_helper.create_and_validate_shipments(test_data_manager, cookie)
        
        trip_id, rider_cookie = self.trip_helper.process_trip_and_shipments(shipment_ids, cookie, self.task_helper, self.auth_helper)
        self.rider_cookie = rider_cookie
        
        self.trip_helper.complete_trip_and_validate(trip_id, rider_cookie)

        self.shipment_helper.validate_shipments_status(
            shipment_ids=shipment_ids,
            expected_status_code=self.shipment_helper.STATUS_CODES["DELIVERED"],
            expected_display_name=self.shipment_helper.DISPLAY_NAMES["DELIVERY_COMPLETED"],
            cookie=cookie
        )

        self.logger.info("=== E2E Test Completed Successfully ===")
