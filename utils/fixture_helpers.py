import pytest
from typing import Dict, Any
from utils.logger_utils import LoggerUtils
from utils.session_manager import SessionManager


class FixtureHelpers:
    
    @staticmethod
    def create_authentication_session(user_type: str, api_client, session_manager: SessionManager) -> Dict[str, Any]:
        logger = LoggerUtils.get_logger(__name__)
        
        try:
            logger.info(f"Setting up {user_type} authentication...")
            
            session_data = session_manager.create_session(user_type)
            
            return {
                "cookie": session_data.cookie,
                "workspace_id": session_data.workspace_id,
                "user_type": session_data.user_type,
                "login_response": session_data.login_response,
                "workspace_response": session_data.workspace_response,
                "session_data": session_data
            }
            
        except Exception as e:
            logger.error(f"{user_type.title()} authentication failed: {str(e)}")
            pytest.fail(f"{user_type.title()} authentication failed: {str(e)}")
    
    @staticmethod
    def cleanup_sessions(session_manager: SessionManager, request) -> None:
        logger = LoggerUtils.get_logger(__name__)
        try:
            test_instance = getattr(request, 'instance', None)
            
            if session_manager.is_session_active("admin"):
                session_manager.logout_session("admin")
            
            if session_manager.is_session_active("rider"):
                session_manager.logout_session("rider")
            
            if test_instance:
                FixtureHelpers._cleanup_test_instance_cookies(test_instance, session_manager, logger)
            
            logger.info("✅ All session cleanup completed successfully")
            
        except Exception as e:
            logger.warning(f"⚠️  Session cleanup failed: {str(e)}")
    
    @staticmethod
    def _cleanup_test_instance_cookies(test_instance, session_manager: SessionManager, logger) -> None:
        try:
            if hasattr(test_instance, 'regular_cookie') and test_instance.regular_cookie:
                logger.info("Found regular_cookie in test instance, attempting logout...")
                try:
                    session_manager.auth_client.logout(test_instance.regular_cookie)
                    logger.info("✅ Regular cookie logout completed")
                except Exception as e:
                    logger.warning(f"⚠️  Regular cookie logout failed: {str(e)}")
            
            if hasattr(test_instance, 'rider_cookie') and test_instance.rider_cookie:
                logger.info("Found rider_cookie in test instance, attempting logout...")
                try:
                    session_manager.auth_client.logout_rider(test_instance.rider_cookie)
                    logger.info("✅ Rider cookie logout completed")
                except Exception as e:
                    logger.warning(f"⚠️  Rider cookie logout failed: {str(e)}")
                    
        except Exception as e:
            logger.warning(f"⚠️  Test instance cookie cleanup failed: {str(e)}")


class TestDataHelpers:
    
    @staticmethod
    def get_test_data(test_data_manager, data_type: str) -> Any:
        return getattr(test_data_manager, f"get_{data_type}_test_data", lambda: None)()
