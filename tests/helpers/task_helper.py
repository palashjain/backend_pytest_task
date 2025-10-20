from typing import Any, Dict, List
from utils.task_client import TaskClient
from utils.logger_utils import LoggerUtils
from test_data.trip_task_data_factory import TripTaskDataFactory


class TaskHelper:
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.task_client = TaskClient(api_client)
        self.logger = LoggerUtils.get_logger(__name__)
        self.data_factory = TripTaskDataFactory()
        
        self.POW_EVENTS: List[str] = [
            "complete_image_proof",
            "complete_notes_proof",
            "complete_signature_proof",
        ]
        self.STATUS_CODE_CREATED: str = "CR"
        self.DISPLAY_PENDING: str = "Pending"
    
    def validate_task_details(self, task_id: str, cookie: str) -> Dict[str, Any]:
        self.logger.info(f"Validating task details for task ID: {task_id}")
        
        result = self.task_client.get_task_details(task_id, cookie)
        
        if result["success"]:
            status_code = result.get("task_status_code")
            display_name = result.get("task_display_name")
            
            if result.get("response_data"):
                self.logger.debug(f"Raw task details response: {result['response_data']}")
            
            self.logger.info(f"Task {task_id} status: {status_code} - {display_name}")
            
            if status_code == self.STATUS_CODE_CREATED and display_name == self.DISPLAY_PENDING:
                self.logger.info(f"✅ Task {task_id} has expected status: Pending")
            else:
                self.logger.warning(f"⚠️ Task {task_id} has unexpected status: {status_code} - {display_name}")
        else:
            self.logger.error(f"Failed to get task details for task {task_id}")
        
        return result
    
    def extract_otp_from_task_details(self, task_id: str, cookie: str) -> str:
        self.logger.info(f"Extracting OTP from task details for task ID: {task_id}")
        
        result = self.task_client.get_task_details(task_id, cookie)
        
        if not (result.get("success") and result.get("response_data")):
            self.logger.error(f"Failed to extract OTP for task {task_id}")
            return ""
        
        response_data = result["response_data"]
        self.logger.debug(f"Task details response for OTP extraction: {response_data}")
        
        try:
            data_array = self._safe_get_data_array(response_data)
            otp_value = self._parse_otp_from_response(data_array)
            if otp_value:
                otp_str = str(otp_value)
                self.logger.info(f"✅ Extracted OTP {otp_str} for task {task_id}")
                return otp_str
        except Exception as e:
            self.logger.error(f"Error extracting OTP from task details: {str(e)}")
        
        self.logger.error(f"Failed to extract OTP for task {task_id}")
        return ""
    
    def process_task_workflow(self, task_id: str, task_type: str, rider_cookie: str) -> bool:
        self.logger.info(f"Processing task workflow for task {task_id} (type: {task_type})")
        
        if not self._update_task_status(task_id, "start", rider_cookie, success_log=f"✅ Task {task_id} started"):
            return False
        
        if not self._perform_pow_steps(task_id, rider_cookie):
            return False
        
        if task_type == "drop":
            self.logger.info(f"Processing OTP for drop task {task_id}")
            otp_value = self.extract_otp_from_task_details(task_id, rider_cookie)
            if not otp_value:
                self.logger.error(f"Failed to extract OTP for drop task {task_id}")
                return False
            otp_data = self.data_factory.create_task_otp_data(otp=otp_value)
            otp_result = self.task_client.submit_task_otp(task_id, otp_data, rider_cookie)
            if not otp_result.get("success"):
                self.logger.error(f"Failed to submit OTP for task {task_id}")
                return False
            self.logger.info(f"✅ OTP {otp_value} submitted for drop task {task_id}")
        
        if not self._update_task_status(task_id, "complete", rider_cookie, success_log=f"✅ Task {task_id} completed successfully"):
            return False
        return True

    def _update_task_status(self, task_id: str, event: str, rider_cookie: str, *, success_log: str = "") -> bool:
        status_data = self.data_factory.create_task_status_data(task_id, event)
        result = self.task_client.update_task_status(status_data, rider_cookie)
        if result.get("success"):
            if success_log:
                self.logger.info(success_log)
            return True
        self.logger.error(f"Failed to update task {task_id} with event '{event}'")
        return False

    def _perform_pow_steps(self, task_id: str, rider_cookie: str) -> bool:
        for event in self.POW_EVENTS:
            if not self._update_task_status(task_id, event, rider_cookie, success_log=f"✅ Task {task_id} - {event} completed"):
                return False
        return True

    def _safe_get_data_array(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        data_array = response_data.get("data", [])
        if not (isinstance(data_array, list) and len(data_array) > 0):
            raise ValueError("Data array missing or empty in response")
        return data_array

    def _parse_otp_from_response(self, data_array: List[Dict[str, Any]]) -> str:
        task_data = data_array[0]
        proofs_of_work = task_data.get("proofs_of_work", {})
        otp_array = proofs_of_work.get("otp", [])
        self.logger.info(f"Found OTP array with {len(otp_array)} entries")
        if not (isinstance(otp_array, list) and len(otp_array) > 0):
            return ""
        otp_entry = otp_array[0]
        otp_meta = otp_entry.get("meta", {})
        otp_value = otp_meta.get("otp")
        self.logger.info(f"OTP meta: {otp_meta}")
        return str(otp_value) if otp_value else ""
