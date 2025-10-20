import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from utils.trip_client import TripClient
from utils.logger_utils import LoggerUtils
from test_data.trip_task_data_factory import TripTaskDataFactory
from tests.helpers.shipment_helper import ShipmentHelper


class TripHelper:

    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 5
    
    STATUS_CODES = {
        'CREATED': 'CR',
        'COMPLETED': 'C',
        'DRIVER_ASSIGNED': 'RA'
    }
    
    DISPLAY_NAMES = {
        'PENDING': 'Pending',
        'COMPLETED': 'Completed',
        'DRIVER_ASSIGNED': 'Driver Assigned'
    }
    
    TRIP_STATUSES = {
        'CREATED': 'C',
        'COMPLETED': 'C'
    }
    
    VEHICLE_STATUSES = {
        'IDLE': 'idle'
    }
    
    RIDER_STATUSES = {
        'IDLE': 'idle'
    }
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.trip_client = TripClient(api_client)
        self.logger = LoggerUtils.get_logger(__name__)
        self.data_factory = TripTaskDataFactory()
    
    def create_trip_for_shipments(self, shipment_ids: List[str], cookie: str) -> Dict[str, Any]:
        self.logger.info(f"Creating trip for shipments: {shipment_ids}")
        
        trip_data = self.data_factory.create_trip_data(shipment_ids)
        result = self.trip_client.create_trip(trip_data, cookie)
        
        self._log_operation_result("Trip creation", result, 
                                  success_msg=lambda: f"Trip created successfully with ID: {result.get('trip_id')}")
        
        return result
    
    def get_trip_info_for_shipment(self, shipment_id: str, cookie: str) -> Dict[str, Any]:
        self.logger.info(f"Getting trip info for shipment: {shipment_id}")
        
        return self._execute_with_retry(
            operation_name=f"get_trip_info_{shipment_id}",
            operation=lambda: self.trip_client.get_trip_info(shipment_id, cookie),
            success_validator=self._validate_trip_info_response,
            failure_handler=lambda: {"success": False, "error": "All retry attempts failed"}
        )
    
    def start_trip(self, trip_id: str, rider_cookie: str) -> Dict[str, Any]:
        self.logger.info(f"Starting trip: {trip_id}")
        
        trip_status_data = self.data_factory.create_trip_status_data(trip_id, "start")
        result = self.trip_client.update_trip_status(trip_status_data, rider_cookie)
        
        self._log_operation_result("Trip start", result, 
                                  success_msg=lambda: f"✅ Trip {trip_id} started successfully")
        
        return result
    
    def complete_trip(self, trip_id: str, rider_cookie: str) -> Dict[str, Any]:
        self.logger.info(f"Completing trip: {trip_id}")
        
        trip_status_data = self.data_factory.create_trip_status_data(trip_id, "complete")
        result = self.trip_client.update_trip_status(trip_status_data, rider_cookie)
        
        self._log_operation_result("Trip completion", result, 
                                  success_msg=lambda: f"✅ Trip {trip_id} completed successfully")
        
        return result

    def process_trip_and_shipments(self, shipment_ids: List[str], cookie: str, 
                                 task_helper: Any, auth_helper: Any) -> Tuple[str, str]:
        self.logger.info("=== Starting Trip and Shipments Processing ===")
        
        trip_result = self.create_trip_for_shipments(shipment_ids, cookie)
        self._assert_success(trip_result, "Trip creation failed")
        
        trip_id = None
        rider_cookie = None
        
        for i, shipment_id in enumerate(shipment_ids):
            self.logger.info(f"=== Processing Shipment {shipment_id} ({i+1}/{len(shipment_ids)}) ===")
            
            trip_id, rider_cookie = self._process_single_shipment(
                shipment_id, shipment_ids, cookie, task_helper, auth_helper, rider_cookie
            )
            
            self.logger.info(f"✅ Successfully completed workflow for shipment {shipment_id}")
        
        return trip_id, rider_cookie

    def process_tasks_for_shipment(self, task_ids: List[str], trip_id: str, 
                                 rider_cookie: str, task_helper: Any) -> None:
        self.logger.info(f"=== Processing Tasks for Trip {trip_id} ===")
        
        for i, task_id in enumerate(task_ids):
            task_type = "pickup" if i % 2 == 0 else "drop"
            self.logger.info(f"Processing task {task_id} (type: {task_type})")
            
            task_success = task_helper.process_task_workflow(task_id, task_type, rider_cookie)
            self._assert_success({"success": task_success}, f"Failed to complete task workflow for task {task_id}")

    def complete_trip_and_validate(self, trip_id: str, rider_cookie: str) -> None:
        self.logger.info(f"=== Completing Trip {trip_id} ===")
        
        complete_trip_result = self.complete_trip(trip_id, rider_cookie)
        self._assert_success(complete_trip_result, f"Failed to complete trip {trip_id}")
        
        self._validate_trip_completion_response(complete_trip_result)

    def validate_trip_status(self, trip_id: str, user_cookie: str, workflow_stage: str = "initial") -> Dict[str, Any]:
        self.logger.info(f"=== Validating Trip Status for Trip {trip_id} (Stage: {workflow_stage}) ===")
        
        trip_status_result = self.trip_client.fetch_trip_status(trip_id, user_cookie)
        self._assert_success(trip_status_result, f"Failed to fetch trip status for trip {trip_id}")
        
        response_data = trip_status_result.get("response_data", {})
        self.logger.info(f"Trip status response: {response_data}")
        
        trip_data = self._extract_trip_data_from_response(response_data)
        shipment_pairs = self._organize_tasks_into_shipment_pairs(trip_data["tasks"])
        
        self._validate_trip_status_by_stage(shipment_pairs, workflow_stage)
        
        self._log_trip_status_summary(trip_data, shipment_pairs, workflow_stage)
        
        self.logger.info("✅ Trip status validation completed successfully")
        return trip_status_result
    
    def _validate_shipment_pairs_by_stage(self, shipment_pairs: List[Dict[str, Any]], expected_status_code: str, expected_display_name: str):
        if not shipment_pairs:
            self.logger.warning("No shipment pairs found to validate")
            return
        
        for i, pair in enumerate(shipment_pairs):
            shipment_num = pair["shipment_number"]
            pickup_task = pair["pickup"]
            drop_task = pair["drop"]
            
            self.logger.info(f"Validating Shipment {shipment_num} pair:")
            
            self._validate_single_task(pickup_task, "pickup", expected_status_code, expected_display_name)
            
            self._validate_single_task(drop_task, "drop", expected_status_code, expected_display_name)
            
            self.logger.info(f"✅ Shipment {shipment_num} pair validation passed")
    
    def _validate_shipment_pairs_mixed(self, shipment_pairs: List[Dict[str, Any]]):
        if not shipment_pairs:
            self.logger.warning("No shipment pairs found to validate")
            return
        
        completed_shipments = 0
        pending_shipments = 0
        
        for i, pair in enumerate(shipment_pairs):
            shipment_num = pair["shipment_number"]
            pickup_task = pair["pickup"]
            drop_task = pair["drop"]
            
            self.logger.info(f"Validating Shipment {shipment_num} pair:")
            
            if i == 0:
                expected_status_code = self.STATUS_CODES['COMPLETED']
                expected_display_name = self.DISPLAY_NAMES['COMPLETED']
                expected_state = "Completed"
                completed_shipments += 1
            else:
                expected_status_code = self.STATUS_CODES['CREATED']
                expected_display_name = self.DISPLAY_NAMES['PENDING']
                expected_state = "Pending"
                pending_shipments += 1
            
            self._validate_single_task(pickup_task, "pickup", expected_status_code, expected_display_name)
            
            self._validate_single_task(drop_task, "drop", expected_status_code, expected_display_name)
            
            self.logger.info(f"✅ Shipment {shipment_num} pair validation passed ({expected_state})")
        
        assert completed_shipments > 0, "Expected at least one completed shipment in partial stage"
        assert pending_shipments > 0, "Expected at least one pending shipment in partial stage"
        
        self.logger.info(f"✅ Shipment pairs validation summary: {completed_shipments} completed, {pending_shipments} pending")
    
    def _validate_single_task(self, task: Dict[str, Any], task_type: str, expected_status_code: str, expected_display_name: str):
        task_id = task.get('id', 'Unknown ID')
        task_number = task.get('task_number', 'Unknown Number')
        self.logger.info(f"  Validating {task_type} task: ID={task_id}, Number={task_number}")
        
        assert "status" in task, f"{task_type.title()} task should contain 'status' field"
        status = task["status"]
        
        assert "status_code" in status, f"{task_type.title()} task status should contain 'status_code'"
        status_code = status["status_code"]
        assert status_code == expected_status_code, f"Expected {task_type.title()} task status_code '{expected_status_code}', got '{status_code}'"
        
        assert "display_name" in status, f"{task_type.title()} task status should contain 'display_name'"
        display_name = status["display_name"]
        assert display_name == expected_display_name, f"Expected {task_type.title()} task display_name '{expected_display_name}', got '{display_name}'"
        
        self.logger.info(f"    - Status Code: '{status_code}' ✅")
        self.logger.info(f"    - Display Name: '{display_name}' ✅")
    
    def _log_operation_result(self, operation_name: str, result: Dict[str, Any], 
                             success_msg: Callable[[], str]) -> None:
        if result.get("success"):
            self.logger.info(success_msg())
        else:
            self.logger.error(f"Failed {operation_name.lower()}: {result}")
    
    def _execute_with_retry(self, operation_name: str, operation: Callable, 
                          success_validator: Callable, failure_handler: Callable) -> Any:
        for attempt in range(self.MAX_RETRIES):
            self.logger.info(f"{operation_name} attempt {attempt + 1}/{self.MAX_RETRIES}")
            
            try:
                result = operation()
                
                if result.get("success") and success_validator(result):
                    self.logger.info(f"{operation_name} successful")
                    return result
                else:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {result}")
                    
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed with exception: {str(e)}")
            
            if attempt < self.MAX_RETRIES - 1:
                self.logger.info(f"Retrying {operation_name} in {self.RETRY_DELAY_SECONDS} seconds...")
                time.sleep(self.RETRY_DELAY_SECONDS)
            else:
                self.logger.error(f"All {operation_name} attempts failed")
        
        return failure_handler()
    
    def _validate_trip_info_response(self, result: Dict[str, Any]) -> bool:
        task_ids = result.get('task_ids', [])
        trip_id = result.get('trip_id')
        status = result.get('status')
        
        if result.get("response_data"):
            self.logger.info(f"Raw trip info response: {result['response_data']}")
        
        if task_ids and trip_id and status:
            self.logger.info(f"Trip info retrieved successfully - Status: {status}, "
                           f"Task IDs: {task_ids}, Trip ID: {trip_id}")
            return True
        else:
            self.logger.warning(f"Trip info returned empty data: "
                              f"Status: {status}, Task IDs: {task_ids}, Trip ID: {trip_id}")
            return False
    
    def _assert_success(self, result: Dict[str, Any], error_message: str) -> None:
        assert result.get("success", False), f"{error_message}: {result}"
    
    def _process_single_shipment(self, shipment_id: str, shipment_ids: List[str], 
                               cookie: str, task_helper: Any, auth_helper: Any,
                               current_rider_cookie: Optional[str]) -> Tuple[str, str]:
        trip_info = self.get_trip_info_for_shipment(shipment_id, cookie)
        self._assert_success(trip_info, f"Failed to get trip info for shipment {shipment_id}")
        
        expected_status = self.DISPLAY_NAMES['DRIVER_ASSIGNED'] if shipment_id == shipment_ids[0] else "In Progress"
        assert trip_info["status"] == expected_status, f"Expected '{expected_status}', got {trip_info['status']}"
        
        task_ids = trip_info["task_ids"]
        trip_id = trip_info["trip_id"]
        
        assert len(task_ids) >= 2, f"Expected at least 2 tasks, got {len(task_ids)}"
        assert trip_id is not None, "Trip ID should not be None"

        self._validate_all_task_details(task_ids, cookie, task_helper)
        
        shipment_helper = ShipmentHelper(self.api_client)
        shipment_helper.validate_shipments_status(
            shipment_ids=[shipment_id],
            expected_status_code=shipment_helper.STATUS_CODES['DRIVER_ASSIGNED'],
            expected_display_name=shipment_helper.DISPLAY_NAMES['DRIVER_ASSIGNED'],
            cookie=cookie
        )
        
        rider_cookie = current_rider_cookie
        if shipment_id == shipment_ids[0]:
            rider_cookie = self._authenticate_and_start_trip(trip_id, auth_helper)
            self._validate_trip_status_after_start(trip_id, cookie)
        
        self.process_tasks_for_shipment(task_ids, trip_id, rider_cookie, task_helper)
        
        self._validate_trip_status_by_shipment_position(shipment_id, shipment_ids, trip_id, cookie)
        
        return trip_id, rider_cookie
    
    def _validate_all_task_details(self, task_ids: List[str], cookie: str, task_helper: Any) -> None:
        for task_id in task_ids:
            task_details = task_helper.validate_task_details(task_id, cookie)
            self._assert_success(task_details, f"Failed to get task details for task {task_id}")
            
            assert task_details["task_status_code"] == self.STATUS_CODES['CREATED'], \
                f"Expected status '{self.STATUS_CODES['CREATED']}', got {task_details['task_status_code']}"
            assert task_details["task_display_name"] == self.DISPLAY_NAMES['PENDING'], \
                f"Expected '{self.DISPLAY_NAMES['PENDING']}', got {task_details['task_display_name']}"
    

    def _authenticate_and_start_trip(self, trip_id: str, auth_helper: Any) -> str:
        self.logger.info("=== Authenticating as Rider ===")
        rider_cookie = auth_helper.authenticate_rider()
        assert rider_cookie is not None, "Rider authentication failed"
        
        self.logger.info(f"=== Starting Trip {trip_id} ===")
        start_trip_result = self.start_trip(trip_id, rider_cookie)
        self._assert_success(start_trip_result, f"Failed to start trip {trip_id}")
        
        return rider_cookie
    
    def _validate_trip_status_after_start(self, trip_id: str, cookie: str) -> None:
        self.logger.info("=== Validating Trip Status After Start ===")
        trip_status_result = self.validate_trip_status(trip_id, cookie, "initial")
        self._assert_success(trip_status_result, f"Trip status validation failed for trip {trip_id}")
    
    def _validate_trip_status_by_shipment_position(self, shipment_id: str, shipment_ids: List[str], 
                                                 trip_id: str, cookie: str) -> None:
        if shipment_id == shipment_ids[-1]:
            self.logger.info("=== Validating Trip Status After All Tasks Complete ===")
            trip_status_result = self.validate_trip_status(trip_id, cookie, "complete")
            self._assert_success(trip_status_result, f"Final trip status validation failed for trip {trip_id}")
        else:
            self.logger.info("=== Validating Trip Status After Partial Task Processing ===")
            trip_status_result = self.validate_trip_status(trip_id, cookie, "partial")
            self._assert_success(trip_status_result, f"Partial trip status validation failed for trip {trip_id}")
    
    def _validate_trip_completion_response(self, complete_trip_result: Dict[str, Any]) -> None:
        self.logger.info("=== Validating Trip Completion Response Status ===")
        
        response_data = complete_trip_result.get("response_data", {})
        self.logger.info(f"Complete trip response: {response_data}")
        
        assert "data" in response_data, "Response should contain 'data' field"
        data_array = response_data["data"]
        assert isinstance(data_array, list) and len(data_array) > 0, "Data should be a non-empty array"
        
        trip_data = data_array[0]
        assert "updated_status" in trip_data, "Trip data should contain 'updated_status' field"
        
        updated_status = trip_data["updated_status"]
        
        trip_status = updated_status.get("trip")
        assert trip_status == self.TRIP_STATUSES['COMPLETED'], f"Expected trip status '{self.TRIP_STATUSES['COMPLETED']}', got '{trip_status}'"
        
        vehicle_status = updated_status.get("vehicle")
        assert vehicle_status == self.VEHICLE_STATUSES['IDLE'], f"Expected vehicle status '{self.VEHICLE_STATUSES['IDLE']}', got '{vehicle_status}'"
        
        rider_status = updated_status.get("rider")
        assert rider_status == self.RIDER_STATUSES['IDLE'], f"Expected rider status '{self.RIDER_STATUSES['IDLE']}', got '{rider_status}'"
        
        self.logger.info("✅ Trip completion status validation passed:")
        self.logger.info(f"   - Trip Status: '{trip_status}' ✅")
        self.logger.info(f"   - Vehicle Status: '{vehicle_status}' ✅")
        self.logger.info(f"   - Rider Status: '{rider_status}' ✅")
    
    def _extract_trip_data_from_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        assert "data" in response_data, "Response should contain 'data' field"
        data = response_data["data"]
        
        assert "tasks" in data, "Data should contain 'tasks' field"
        tasks = data["tasks"]
        assert isinstance(tasks, list) and len(tasks) > 0, "Tasks should be a non-empty list"
        
        current_task = data.get("current_task", 0)
        total_tasks = data.get("total_tasks", len(tasks))
        self.logger.info(f"Trip Progress: {current_task}/{total_tasks} tasks")
        
        return data
    
    def _organize_tasks_into_shipment_pairs(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pickup_tasks = []
        drop_tasks = []
        
        for task in tasks:
            task_type = task.get("task_type", "").lower()
            if task_type == "pickup":
                pickup_tasks.append(task)
            elif task_type == "drop":
                drop_tasks.append(task)
        
        shipment_pairs = []
        for i in range(len(pickup_tasks)):
            if i < len(drop_tasks):
                shipment_pairs.append({
                    "pickup": pickup_tasks[i],
                    "drop": drop_tasks[i],
                    "shipment_number": i + 1
                })
        
        self.logger.info(f"Found {len(shipment_pairs)} shipment pairs (pickup + drop)")
        assert len(pickup_tasks) == len(drop_tasks), f"Expected equal pickup and drop tasks, got {len(pickup_tasks)} pickup and {len(drop_tasks)} drop"
        
        return shipment_pairs
    
    def _validate_trip_status_by_stage(self, shipment_pairs: List[Dict[str, Any]], workflow_stage: str) -> None:
        if workflow_stage == "initial":
            self._validate_shipment_pairs_by_stage(shipment_pairs, self.STATUS_CODES['CREATED'], self.DISPLAY_NAMES['PENDING'])
        elif workflow_stage == "partial":
            self._validate_shipment_pairs_mixed(shipment_pairs)
        elif workflow_stage == "complete":
            self._validate_shipment_pairs_by_stage(shipment_pairs, self.STATUS_CODES['COMPLETED'], self.DISPLAY_NAMES['COMPLETED'])
    
    def _log_trip_status_summary(self, trip_data: Dict[str, Any], shipment_pairs: List[Dict[str, Any]], 
                               workflow_stage: str) -> None:
        self.logger.info("=== Trip Status Validation Summary ===")
        self.logger.info(f"Total tasks in trip: {len(trip_data['tasks'])}")
        self.logger.info(f"Shipment pairs: {len(shipment_pairs)}")
        self.logger.info(f"Workflow stage: {workflow_stage}")
