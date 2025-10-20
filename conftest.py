import pytest
import shutil
from pathlib import Path
from typing import Dict, Any
from utils.api_client import APIClient
from utils.logger_utils import LoggerUtils
from utils.session_manager import SessionManager
from utils.fixture_helpers import FixtureHelpers
from test_data.generic_data_manager import GenericDataManager

@pytest.fixture(scope="session")
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture(scope="session")
def test_data_manager() -> GenericDataManager:
    return GenericDataManager()


@pytest.fixture(scope="session")
def session_manager(api_client: APIClient) -> SessionManager:
    return SessionManager(api_client)


@pytest.fixture(scope="function")
def authenticated_request(api_client: APIClient, session_manager: SessionManager) -> Dict[str, Any]:
    return FixtureHelpers.create_authentication_session("admin", api_client, session_manager)


@pytest.fixture(scope="function")
def authenticated_rider_request(api_client: APIClient, session_manager: SessionManager) -> Dict[str, Any]:
    return FixtureHelpers.create_authentication_session("rider", api_client, session_manager)


@pytest.fixture(scope="function")
def valid_shipment_data(test_data_manager: GenericDataManager) -> Dict[str, Any]:
    return test_data_manager.get_shipment_test_data()


@pytest.fixture(autouse=True)
def inject_dependencies(api_client: APIClient, session_manager: SessionManager, request):
    if hasattr(request, 'instance') and request.instance is not None:
        request.instance.api_client = api_client
        request.instance.session_manager = session_manager


@pytest.fixture(autouse=True)
def test_logging(request):
    test_name = request.node.name
    
    LoggerUtils.log_test_start(test_name)
    
    yield
    
    LoggerUtils.log_test_end(test_name, "completed")


@pytest.fixture(autouse=True)
def session_cleanup(session_manager: SessionManager, request):
    yield
    FixtureHelpers.cleanup_sessions(session_manager, request)


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
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
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


def pytest_sessionfinish(session, exitstatus):
    logger = LoggerUtils.get_logger(__name__)
    logger.info(f"=== Test Session Finished with exit status: {exitstatus} ===")
    logger.info("ℹ️  Allure results preserved in 'allure-results' folder")


pytestmark = [
    pytest.mark.shipment,
    pytest.mark.regression,
    pytest.mark.e2e
]
