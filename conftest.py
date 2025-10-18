import pytest
import shutil
from pathlib import Path
from typing import Dict, Any
from utils.api_client import APIClient
from utils.auth_client import AuthClient
from utils.logger_utils import LoggerUtils
from test_data.generic_data_manager import GenericDataManager


@pytest.fixture(scope="session")
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(scope="session")
def test_data_manager() -> GenericDataManager:
    return GenericDataManager()


@pytest.fixture(scope="function")
def authenticated_request(api_client: APIClient) -> Dict[str, Any]:
    logger = LoggerUtils.get_logger(__name__)
    auth_client = AuthClient(api_client)
    
    try:
        logger.info("Starting function-level authentication...")
        
        api_client.clear_session()
        
        auth_data = auth_client.login()
        
        if not auth_data.get("cookie") or not auth_data.get("workspace_id"):
            pytest.fail("Authentication failed: Missing cookie or workspace ID")
        
        workspace_auth_data = auth_client.workspace_login(
            auth_data["workspace_id"], 
            auth_data["cookie"]
        )
        
        session_data = {
            "cookie": workspace_auth_data["cookie"],
            "workspace_id": auth_data["workspace_id"],
            "login_response": auth_data["response_data"],
            "workspace_response": workspace_auth_data["response_data"]
        }
        
        logger.info("Function-level authentication completed successfully")
        return session_data
        
    except Exception as e:
        logger.error(f"Function-level authentication failed: {str(e)}")
        pytest.fail(f"Function-level authentication failed: {str(e)}")


@pytest.fixture(scope="function")
def valid_shipment_data(test_data_manager: GenericDataManager) -> Dict[str, Any]:
    return test_data_manager.get_shipment_test_data()


@pytest.fixture(autouse=True)
def test_logging(request):
    test_name = request.node.name
    
    LoggerUtils.log_test_start(test_name)
    
    yield
    
    LoggerUtils.log_test_end(test_name, "completed")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression test"
    )
    config.addinivalue_line(
        "markers", "shipment: mark test as shipment API test"
    )

def cleanup_allure_results_folder():
    project_root = Path(__file__).parent
    allure_results_dir = project_root / "allure-results"
    
    logger = LoggerUtils.get_logger(__name__)
    
    if allure_results_dir.exists():
        try:
            shutil.rmtree(allure_results_dir)
            logger.info(f"🧹 Cleaned up: {allure_results_dir}")
        except Exception as e:
            logger.warning(f"❌ Error cleaning allure-results: {e}")
    else:
        logger.info("ℹ️  No allure-results folder found to clean up")
    
    try:
        allure_results_dir.mkdir(exist_ok=True)
        logger.info(f"📁 Created: {allure_results_dir}")
    except Exception as e:
        logger.warning(f"❌ Error creating allure-results folder: {e}")


def pytest_sessionstart(session):
    cleanup_allure_results_folder()
    
    log_file_path = LoggerUtils.initialize_session_logging()
    logger = LoggerUtils.get_logger(__name__)
    logger.info("=== Test Session Started ===")
    logger.info(f"Main log file: {log_file_path}")
    logger.info(f"Request log file: {LoggerUtils._session_request_log_file}")
    logger.info(f"Response log file: {LoggerUtils._session_response_log_file}")


def pytest_sessionfinish(session,exitstatus):
    logger = LoggerUtils.get_logger(__name__)
    logger.info(f"=== Test Session Finished with exit status: {exitstatus} ===")
    logger.info("ℹ️  Allure results preserved in 'allure-results' folder")


pytestmark = [
    pytest.mark.shipment,
    pytest.mark.regression
]